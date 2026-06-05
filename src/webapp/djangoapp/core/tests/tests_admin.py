from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse

from djangoapp.core.admin import IssueAdmin, IssueStateTransitionAdmin
from djangoapp.core.models import Collection, Issue, IssueCategory, IssueStateTransition, WorkflowState


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

    def test_issue_admin_save_model_creates_issue_on_add(self):
        admin_instance = IssueAdmin(Issue, self.site)
        request = self.request_factory.post("/admin/core/issue/add/")
        request.user = self.admin_user
        issue = Issue(
            title="Create issue from admin",
            collection=self.collection,
            category=self.category,
        )

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

        admin_instance.save_model(request, issue, form=None, change=True)

        updated_issue = Issue.objects.get(pk=self.issue.pk)
        transition = IssueStateTransition.objects.get(issue=updated_issue)

        self.assertEqual(updated_issue.workflow_state, WorkflowState.CLOSED)
        self.assertEqual(updated_issue.title, "Closed from admin")
        self.assertEqual(transition.to_state, WorkflowState.CLOSED)
        self.assertEqual(transition.changed_by_user, self.admin_user)

    def test_issue_admin_save_model_updates_without_transition_when_state_unchanged(self):
        admin_instance = IssueAdmin(Issue, self.site)
        request = self.request_factory.post(f"/admin/core/issue/{self.issue.pk}/change/")
        request.user = self.admin_user
        issue = Issue.objects.get(pk=self.issue.pk)
        issue.title = "Updated title"

        admin_instance.save_model(request, issue, form=None, change=True)

        updated_issue = Issue.objects.get(pk=self.issue.pk)

        self.assertEqual(updated_issue.title, "Updated title")
        self.assertEqual(IssueStateTransition.objects.count(), 0)

    def test_issue_state_transition_admin_disables_manual_adds(self):
        admin_instance = IssueStateTransitionAdmin(IssueStateTransition, self.site)

        self.assertFalse(admin_instance.has_add_permission(request=None))
