from unittest.mock import patch

from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse

from djangoapp.core.admin import (
    GroupAdminForm,
    IssueAdmin,
    IssueHistoryEventAdmin,
    IssueStateTransitionAdmin,
    WebhookDeliveryAttemptAdmin,
    WebhookEndpointAdmin,
    WebhookEndpointAdminForm,
    WebhookEndpointEventTypeFilter,
    WebhookEventAdmin,
)
from djangoapp.core.models import (
    Collection,
    Issue,
    IssueCategory,
    IssueDescriptionTemplate,
    IssueHistoryEvent,
    IssueStateTransition,
    WebhookDeliveryAttempt,
    WebhookEndpoint,
    WebhookEvent,
    WebhookEventType,
    WorkflowState,
)


class CoreAdminTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.admin_user = self.user_model.objects.create_superuser(
            username="admin",
            password="demo-password-123",
            email="admin@example.com",
        )
        self.group = Group.objects.create(name="Network Operations")
        self.admin_user.groups.add(self.group)
        self.category = IssueCategory.objects.create(
            name="Service Request",
            code="SRV",
        )
        self.collection = Collection.objects.get(prefix="TASK")
        self.issue = Issue.objects.create(
            title="VPN access request",
            collection=self.collection,
            category=self.category,
        )
        self.site = AdminSite()
        self.request_factory = RequestFactory()

    def test_issue_admin_changelist_is_available(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin:core_issue_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.issue.issue_number)

    def test_admin_uses_application_name_in_title(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"<title>{settings.PRODUCT_DISPLAY_NAME} - Administration</title>", html=True)
        self.assertContains(
            response,
            f'<div id="site-name"><a href="{reverse("admin:index")}">{settings.PRODUCT_DISPLAY_NAME} - Administration</a></div>',
            html=True,
        )

    def test_issue_category_admin_changelist_is_available(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin:core_issuecategory_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.category.name)

    def test_issue_description_template_admin_changelist_is_available(self):
        IssueDescriptionTemplate.objects.create(
            name="VPN access request",
            description_markdown="## Request details",
            category=self.category,
        )
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin:core_issuedescriptiontemplate_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VPN access request")

    def test_group_admin_change_form_shows_description_and_persists_updates(self):
        form = GroupAdminForm(instance=self.group)

        self.assertEqual(form.fields["description"].initial, "")

        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("admin:auth_group_change", args=[self.group.pk]),
            {
                "name": self.group.name,
                "description": "Handles escalated network cases",
                "permissions": [],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.group.refresh_from_db()
        self.assertEqual(self.group.core_details.description, "Handles escalated network cases")

        updated_form = GroupAdminForm(instance=self.group)

        self.assertEqual(updated_form.fields["description"].initial, "Handles escalated network cases")

    def test_issue_admin_save_model_creates_issue_on_add(self):
        admin_instance = IssueAdmin(Issue, self.site)
        request = self.request_factory.post("/admin/core/issue/add/")
        request.user = self.admin_user
        issue = Issue(
            title="Create issue from admin",
            collection=self.collection,
            category=self.category,
        )

        with patch(
            "djangoapp.core.controllers.webhook_delivery_controller.WebhookDeliveryController.dispatch_event_async"
        ):
            admin_instance.save_model(request, issue, form=None, change=False)

        self.assertIsNotNone(issue.pk)
        self.assertEqual(issue.issue_number, "TASK-002")

    def test_issue_admin_save_model_uses_transition_controller_on_state_change(self):
        admin_instance = IssueAdmin(Issue, self.site)
        request = self.request_factory.post(f"/admin/core/issue/{self.issue.pk}/change/")
        request.user = self.admin_user
        issue = Issue.objects.get(pk=self.issue.pk)
        issue.workflow_state = WorkflowState.CLOSED
        issue.group = self.group
        issue.user = self.admin_user
        issue.title = "Closed from admin"

        with patch(
            "djangoapp.core.controllers.webhook_delivery_controller.WebhookDeliveryController.dispatch_event_async"
        ):
            admin_instance.save_model(request, issue, form=None, change=True)

        updated_issue = Issue.objects.get(pk=self.issue.pk)
        transition = IssueStateTransition.objects.get(issue=updated_issue)

        self.assertEqual(updated_issue.workflow_state, WorkflowState.CLOSED)
        self.assertEqual(updated_issue.title, "Closed from admin")
        self.assertEqual(transition.to_state, WorkflowState.CLOSED)
        self.assertEqual(transition.changed_by_user, self.admin_user)
        self.assertGreaterEqual(updated_issue.history_events.count(), 3)
        self.assertEqual(
            set(updated_issue.history_events.values_list("field_name", flat=True)),
            {"title", "group", "user", "closed_at"},
        )

    def test_issue_admin_save_model_updates_without_transition_when_state_unchanged(self):
        admin_instance = IssueAdmin(Issue, self.site)
        request = self.request_factory.post(f"/admin/core/issue/{self.issue.pk}/change/")
        request.user = self.admin_user
        issue = Issue.objects.get(pk=self.issue.pk)
        issue.title = "Updated title"

        with patch(
            "djangoapp.core.controllers.webhook_delivery_controller.WebhookDeliveryController.dispatch_event_async"
        ):
            admin_instance.save_model(request, issue, form=None, change=True)

        updated_issue = Issue.objects.get(pk=self.issue.pk)

        self.assertEqual(updated_issue.title, "Updated title")
        self.assertEqual(IssueStateTransition.objects.count(), 0)

    def test_issue_state_transition_admin_disables_manual_adds(self):
        admin_instance = IssueStateTransitionAdmin(IssueStateTransition, self.site)

        self.assertFalse(admin_instance.has_add_permission(request=None))

    def test_issue_history_event_admin_disables_manual_adds(self):
        admin_instance = IssueHistoryEventAdmin(IssueHistoryEvent, self.site)

        self.assertFalse(admin_instance.has_add_permission(request=None))

    def test_webhook_endpoint_admin_changelist_is_available(self):
        WebhookEndpoint.objects.create(
            name="Audit sink",
            target_url="https://example.com/webhooks/audit",
            subscribed_event_types=[WebhookEventType.ISSUE_UPDATED],
        )
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin:core_webhookendpoint_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Audit sink")

    def test_webhook_endpoint_admin_preserves_secret_when_blank_on_edit(self):
        endpoint = WebhookEndpoint.objects.create(
            name="Secret sink",
            target_url="https://example.com/webhooks/secret",
            subscribed_event_types=[WebhookEventType.ISSUE_UPDATED],
            secret="initial-secret",
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("admin:core_webhookendpoint_change", args=[endpoint.pk]),
            {
                "name": endpoint.name,
                "description": "",
                "target_url": endpoint.target_url,
                "enabled": "on",
                "disable_ssl_certificate_validation": "on",
                "subscribed_event_types": [WebhookEventType.ISSUE_UPDATED],
                "secret": "",
                "timeout_seconds": endpoint.timeout_seconds,
                "max_retries": endpoint.max_retries,
                "retry_backoff_seconds": endpoint.retry_backoff_seconds,
                "last_delivery_status": endpoint.last_delivery_status,
            },
            follow=True,
        )

        endpoint.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(endpoint.secret, "initial-secret")

    def test_webhook_endpoint_admin_form_allows_blank_secret_on_create(self):
        form = WebhookEndpointAdminForm(
            data={
                "name": "Fresh sink",
                "description": "",
                "target_url": "https://example.com/webhooks/fresh",
                "enabled": True,
                "disable_ssl_certificate_validation": False,
                "subscribed_event_types": [WebhookEventType.ISSUE_CREATED],
                "secret": "",
                "timeout_seconds": 5,
                "max_retries": 3,
                "retry_backoff_seconds": 60,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        endpoint = form.save(commit=False)

        self.assertEqual(endpoint.secret, "")

    def test_webhook_endpoint_admin_form_allows_internal_service_hostname_target_url(self):
        form = WebhookEndpointAdminForm(
            data={
                "name": "Local n8n sink",
                "description": "",
                "target_url": "http://n8n:5678/webhook-test/ea69561c-4574-45d1-b245-093ea574330a/it-operation-ticketing",
                "enabled": True,
                "disable_ssl_certificate_validation": False,
                "subscribed_event_types": [WebhookEventType.ISSUE_CREATED],
                "secret": "",
                "timeout_seconds": 5,
                "max_retries": 3,
                "retry_backoff_seconds": 60,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_webhook_endpoint_event_type_filter_filters_matching_endpoints(self):
        matching_endpoint = WebhookEndpoint.objects.create(
            name="Matching sink",
            target_url="https://example.com/webhooks/matching",
            subscribed_event_types=[WebhookEventType.ISSUE_UPDATED],
        )
        WebhookEndpoint.objects.create(
            name="Other sink",
            target_url="https://example.com/webhooks/other",
            subscribed_event_types=[WebhookEventType.ISSUE_COMMENTED],
        )
        request = self.request_factory.get(
            "/admin/core/webhookendpoint/", {"subscribed_event_type": WebhookEventType.ISSUE_UPDATED}
        )
        admin_instance = WebhookEndpointAdmin(WebhookEndpoint, self.site)
        endpoint_filter = WebhookEndpointEventTypeFilter(
            request,
            {"subscribed_event_type": WebhookEventType.ISSUE_UPDATED},
            WebhookEndpoint,
            admin_instance,
        )
        endpoint_filter.value = lambda: WebhookEventType.ISSUE_UPDATED

        queryset = endpoint_filter.queryset(request, WebhookEndpoint.objects.all())

        self.assertEqual(list(queryset), [matching_endpoint])

    def test_webhook_event_admin_disables_manual_adds(self):
        admin_instance = WebhookEventAdmin(WebhookEvent, self.site)

        self.assertFalse(admin_instance.has_add_permission(request=None))

    def test_webhook_delivery_attempt_admin_disables_manual_adds(self):
        admin_instance = WebhookDeliveryAttemptAdmin(WebhookDeliveryAttempt, self.site)

        self.assertFalse(admin_instance.has_add_permission(request=None))

    def test_webhook_delivery_attempt_admin_helpers_return_event_details(self):
        endpoint = WebhookEndpoint.objects.create(
            name="Attempt sink",
            target_url="https://example.com/webhooks/attempts",
            subscribed_event_types=[WebhookEventType.ISSUE_UPDATED],
        )
        webhook_event = WebhookEvent.objects.create(
            event_type=WebhookEventType.ISSUE_UPDATED,
            issue=self.issue,
            target_endpoint_ids=[endpoint.pk],
            payload={"event": WebhookEventType.ISSUE_UPDATED, "data": {"id": self.issue.pk}},
        )
        delivery_attempt = WebhookDeliveryAttempt.objects.create(
            webhook_endpoint=endpoint,
            webhook_event=webhook_event,
            attempt_number=1,
            request_headers={"Content-Type": "application/json"},
            request_body="{}",
            success=True,
            duration_ms=5,
        )
        admin_instance = WebhookDeliveryAttemptAdmin(WebhookDeliveryAttempt, self.site)

        self.assertEqual(admin_instance.event_type(delivery_attempt), WebhookEventType.ISSUE_UPDATED)
        self.assertEqual(admin_instance.issue_reference(delivery_attempt), self.issue.issue_number)
        self.assertFalse(admin_instance.has_delete_permission(request=None, obj=delivery_attempt))
