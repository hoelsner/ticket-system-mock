import ssl
from unittest.mock import MagicMock, patch
from urllib import error

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from djangoapp.core.controllers import WebhookDeliveryController
from djangoapp.core.models import (
    Collection,
    Issue,
    IssueCategory,
    WebhookDeliveryAttempt,
    WebhookDeliveryStatus,
    WebhookEndpoint,
    WebhookEvent,
    WebhookEventType,
)


class WebhookDeliveryTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="dispatcher",
            password="demo-password-123",
        )
        self.group = Group.objects.create(name="Network Operations")
        self.user.groups.add(self.group)
        self.category = IssueCategory.objects.create(name="Incident", code="INC")
        self.collection = Collection.objects.get(prefix="TASK")
        self.issue = Issue.objects.create(
            title="Webhook delivery issue",
            description_markdown="Delivery target test.",
            collection=self.collection,
            category=self.category,
            group=self.group,
            user=self.user,
        )
        self.endpoint = WebhookEndpoint.objects.create(
            name="Webhook target",
            target_url="https://example.com/webhooks/issues",
            subscribed_event_types=[WebhookEventType.ISSUE_UPDATED],
            secret="shared-secret",
            max_retries=1,
            retry_backoff_seconds=1,
        )
        self.webhook_event = WebhookEvent.objects.create(
            event_type=WebhookEventType.ISSUE_UPDATED,
            issue=self.issue,
            target_endpoint_ids=[self.endpoint.pk],
            payload={
                "event": WebhookEventType.ISSUE_UPDATED,
                "data": {"id": self.issue.pk},
            },
        )

    @patch("djangoapp.core.controllers.webhook_delivery_controller.request.urlopen")
    def test_deliver_event_records_successful_attempt(self, mock_urlopen):
        response = MagicMock()
        response.status = 204
        response.read.return_value = b""
        mock_urlopen.return_value.__enter__.return_value = response

        attempted = WebhookDeliveryController.deliver_event(self.webhook_event.pk)

        self.assertTrue(attempted)
        delivery_attempt = WebhookDeliveryAttempt.objects.get(webhook_event=self.webhook_event)
        self.assertTrue(delivery_attempt.success)
        self.assertEqual(delivery_attempt.response_status_code, 204)
        self.endpoint.refresh_from_db()
        self.webhook_event.refresh_from_db()
        self.assertEqual(self.endpoint.last_delivery_status, WebhookDeliveryStatus.SUCCESS)
        self.assertEqual(self.webhook_event.delivery_status, WebhookDeliveryStatus.SUCCESS)

    @patch("djangoapp.core.controllers.webhook_delivery_controller.request.urlopen")
    def test_deliver_event_stores_signature_header(self, mock_urlopen):
        response = MagicMock()
        response.status = 202
        response.read.return_value = b"accepted"
        mock_urlopen.return_value.__enter__.return_value = response

        WebhookDeliveryController.deliver_event(self.webhook_event.pk)

        delivery_attempt = WebhookDeliveryAttempt.objects.get(webhook_event=self.webhook_event)
        self.assertIn("X-Webhook-Signature", delivery_attempt.request_headers)
        self.assertTrue(delivery_attempt.request_headers["X-Webhook-Signature"].startswith("sha256="))

    @patch("djangoapp.core.controllers.webhook_delivery_controller.request.urlopen")
    def test_deliver_event_uses_default_ssl_validation(self, mock_urlopen):
        response = MagicMock()
        response.status = 204
        response.read.return_value = b""
        mock_urlopen.return_value.__enter__.return_value = response

        WebhookDeliveryController.deliver_event(self.webhook_event.pk)

        self.assertNotIn("context", mock_urlopen.call_args.kwargs)

    @patch("djangoapp.core.controllers.webhook_delivery_controller.request.urlopen")
    def test_deliver_event_can_disable_ssl_certificate_validation(self, mock_urlopen):
        self.endpoint.disable_ssl_certificate_validation = True
        self.endpoint.save(update_fields=["disable_ssl_certificate_validation", "updated_at"])
        response = MagicMock()
        response.status = 204
        response.read.return_value = b""
        mock_urlopen.return_value.__enter__.return_value = response

        WebhookDeliveryController.deliver_event(self.webhook_event.pk)

        ssl_context = mock_urlopen.call_args.kwargs["context"]
        self.assertIsInstance(ssl_context, ssl.SSLContext)
        self.assertFalse(ssl_context.check_hostname)
        self.assertEqual(ssl_context.verify_mode, ssl.CERT_NONE)

    @patch("djangoapp.core.controllers.webhook_delivery_controller.request.urlopen")
    def test_process_pending_events_retries_due_failures(self, mock_urlopen):
        WebhookDeliveryAttempt.objects.create(
            webhook_endpoint=self.endpoint,
            webhook_event=self.webhook_event,
            attempt_number=1,
            request_headers={"Content-Type": "application/json"},
            request_body="{}",
            response_status_code=500,
            response_body="server error",
            error_message="server error",
            success=False,
            duration_ms=5,
            attempted_at=timezone.now() - timezone.timedelta(seconds=10),
        )
        response = MagicMock()
        response.status = 200
        response.read.return_value = b"ok"
        mock_urlopen.return_value.__enter__.return_value = response

        processed = WebhookDeliveryController.process_pending_events()

        self.assertEqual(processed, [str(self.webhook_event.pk)])
        self.assertEqual(
            WebhookDeliveryAttempt.objects.filter(webhook_event=self.webhook_event).count(),
            2,
        )
        self.webhook_event.refresh_from_db()
        self.assertEqual(self.webhook_event.delivery_status, WebhookDeliveryStatus.SUCCESS)

    def test_delivery_status_becomes_failed_after_retry_exhaustion(self):
        self.endpoint.max_retries = 0
        self.endpoint.save(update_fields=["max_retries", "updated_at"])
        WebhookDeliveryAttempt.objects.create(
            webhook_endpoint=self.endpoint,
            webhook_event=self.webhook_event,
            attempt_number=1,
            request_headers={"Content-Type": "application/json"},
            request_body="{}",
            response_status_code=500,
            response_body="server error",
            error_message="server error",
            success=False,
            duration_ms=5,
        )

        attempted = WebhookDeliveryController.deliver_event(self.webhook_event.pk)

        self.assertFalse(attempted)
        self.webhook_event.refresh_from_db()
        self.assertEqual(self.webhook_event.delivery_status, WebhookDeliveryStatus.FAILED)

    @patch("djangoapp.core.controllers.webhook_delivery_controller.threading.Thread")
    def test_dispatch_event_async_starts_daemon_thread(self, mock_thread):
        thread_instance = MagicMock()
        mock_thread.return_value = thread_instance

        WebhookDeliveryController.dispatch_event_async(self.webhook_event.pk)

        mock_thread.assert_called_once()
        thread_instance.start.assert_called_once()

    @patch("djangoapp.core.controllers.webhook_delivery_controller.close_old_connections")
    @patch("djangoapp.core.controllers.webhook_delivery_controller.logger.exception")
    @patch("djangoapp.core.controllers.webhook_delivery_controller.WebhookDeliveryController.deliver_event")
    def test_deliver_event_in_thread_logs_exceptions(
        self, mock_deliver_event, mock_logger_exception, mock_close_connections
    ):
        mock_deliver_event.side_effect = RuntimeError("boom")

        WebhookDeliveryController._deliver_event_in_thread(self.webhook_event.pk)

        mock_logger_exception.assert_called_once()
        self.assertEqual(mock_close_connections.call_count, 2)

    def test_process_pending_events_skips_successful_events(self):
        self.webhook_event.delivery_status = WebhookDeliveryStatus.SUCCESS
        self.webhook_event.save(update_fields=["delivery_status"])

        processed = WebhookDeliveryController.process_pending_events()

        self.assertEqual(processed, [])

    def test_get_target_endpoints_ignores_disabled_and_missing_endpoint_ids(self):
        disabled_endpoint = WebhookEndpoint.objects.create(
            name="Disabled target",
            target_url="https://example.com/webhooks/disabled",
            enabled=False,
            subscribed_event_types=[WebhookEventType.ISSUE_UPDATED],
        )
        self.webhook_event.target_endpoint_ids = [disabled_endpoint.pk, self.endpoint.pk, 999999]
        self.webhook_event.save(update_fields=["target_endpoint_ids"])

        target_endpoints = WebhookDeliveryController._get_target_endpoints(self.webhook_event)

        self.assertEqual([endpoint.pk for endpoint in target_endpoints], [self.endpoint.pk])

    def test_should_attempt_delivery_returns_false_for_successful_attempt(self):
        WebhookDeliveryAttempt.objects.create(
            webhook_endpoint=self.endpoint,
            webhook_event=self.webhook_event,
            attempt_number=1,
            request_headers={"Content-Type": "application/json"},
            request_body="{}",
            response_status_code=200,
            response_body="ok",
            error_message="",
            success=True,
            duration_ms=5,
        )

        should_attempt = WebhookDeliveryController._should_attempt_delivery(self.webhook_event, self.endpoint)

        self.assertFalse(should_attempt)

    def test_should_attempt_delivery_returns_false_when_retry_not_due(self):
        WebhookDeliveryAttempt.objects.create(
            webhook_endpoint=self.endpoint,
            webhook_event=self.webhook_event,
            attempt_number=1,
            request_headers={"Content-Type": "application/json"},
            request_body="{}",
            response_status_code=500,
            response_body="server error",
            error_message="server error",
            success=False,
            duration_ms=5,
            attempted_at=timezone.now(),
        )

        should_attempt = WebhookDeliveryController._should_attempt_delivery(self.webhook_event, self.endpoint)

        self.assertFalse(should_attempt)

    @patch("djangoapp.core.controllers.webhook_delivery_controller.request.urlopen")
    def test_deliver_event_records_http_error_attempt(self, mock_urlopen):
        mock_urlopen.side_effect = error.HTTPError(
            self.endpoint.target_url,
            500,
            "server error",
            hdrs=None,
            fp=MagicMock(read=lambda: b"server error"),
        )

        attempted = WebhookDeliveryController.deliver_event(self.webhook_event.pk)

        self.assertTrue(attempted)
        delivery_attempt = WebhookDeliveryAttempt.objects.get(webhook_event=self.webhook_event)
        self.assertFalse(delivery_attempt.success)
        self.assertEqual(delivery_attempt.response_status_code, 500)
        self.webhook_event.refresh_from_db()
        self.assertEqual(self.webhook_event.delivery_status, WebhookDeliveryStatus.PARTIAL_FAILURE)

    def test_build_request_headers_omits_signature_without_secret(self):
        self.endpoint.secret = ""

        headers = WebhookDeliveryController._build_request_headers(
            self.webhook_event,
            self.endpoint,
            b"{}",
            "1700000000",
        )

        self.assertNotIn("X-Webhook-Signature", headers)

    def test_validate_target_url_rejects_non_http_schemes(self):
        with self.assertRaisesMessage(ValueError, "Webhook target URLs must use http or https."):
            WebhookDeliveryController._validate_target_url("ftp://example.com/webhooks")

    def test_webhook_endpoint_clean_allows_internal_service_hostname_target_url(self):
        endpoint = WebhookEndpoint(
            name="Local n8n sink",
            target_url="http://n8n:5678/webhook-test/ea69561c-4574-45d1-b245-093ea574330a/it-operation-ticketing",
            subscribed_event_types=[WebhookEventType.ISSUE_UPDATED],
        )

        endpoint.full_clean()

    def test_webhook_endpoint_clean_rejects_target_url_without_hostname(self):
        endpoint = WebhookEndpoint(
            name="Broken target",
            target_url="http:///webhooks/broken",
            subscribed_event_types=[WebhookEventType.ISSUE_UPDATED],
        )

        with self.assertRaises(ValidationError):
            endpoint.full_clean()

    def test_webhook_endpoint_clean_rejects_invalid_event_types(self):
        endpoint = WebhookEndpoint(
            name="Invalid events",
            target_url="https://example.com/webhooks/invalid",
            subscribed_event_types=["invalid.event"],
        )

        with self.assertRaises(ValidationError):
            endpoint.full_clean()

    def test_webhook_endpoint_clean_requires_list_event_types(self):
        endpoint = WebhookEndpoint(
            name="Wrong type",
            target_url="https://example.com/webhooks/wrong-type",
            subscribed_event_types="issue.updated",
        )

        with self.assertRaises(ValidationError):
            endpoint.full_clean()

    def test_webhook_event_without_targets_is_marked_success(self):
        self.webhook_event.target_endpoint_ids = []
        self.webhook_event.save(update_fields=["target_endpoint_ids"])

        attempted = WebhookDeliveryController.deliver_event(self.webhook_event.pk)

        self.assertFalse(attempted)
        self.webhook_event.refresh_from_db()
        self.assertEqual(self.webhook_event.delivery_status, WebhookDeliveryStatus.SUCCESS)
