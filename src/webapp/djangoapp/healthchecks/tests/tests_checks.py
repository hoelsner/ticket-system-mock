from unittest.mock import MagicMock, patch
from urllib import error

from django.test import TestCase
from djangoapp.core.models import WebhookEndpoint
from djangoapp.healthchecks.checks import HealthcheckService


class HealthcheckServiceTests(TestCase):
    @patch("djangoapp.healthchecks.checks.connection.cursor")
    def test_database_check_hides_sensitive_exception_details(self, mock_cursor):
        mock_cursor.side_effect = RuntimeError("password=secret")

        result = HealthcheckService.run_database_check()

        self.assertEqual(result.status, "unhealthy")
        self.assertEqual(result.message, "Database connectivity check failed.")
        self.assertEqual(result.exception_type, "RuntimeError")

    @patch("djangoapp.healthchecks.checks.MigrationExecutor")
    def test_migration_check_reports_pending_migrations(self, mock_executor_class):
        mock_executor = mock_executor_class.return_value
        mock_executor.loader.graph.leaf_nodes.return_value = [("core", "0001_initial")]
        mock_executor.migration_plan.return_value = [(("core", "0001_initial"), False)]

        result = HealthcheckService.run_migration_check()

        self.assertEqual(result.status, "unhealthy")
        self.assertEqual(result.message, "Pending migrations detected.")

    @patch("djangoapp.healthchecks.checks.caches")
    def test_cache_check_reports_read_write_mismatch(self, mock_caches):
        mock_cache = MagicMock()
        mock_cache.get.return_value = "wrong-value"
        mock_caches.__getitem__.return_value = mock_cache

        result = HealthcheckService.run_cache_check()

        self.assertEqual(result.status, "unhealthy")
        self.assertEqual(result.message, "Cache read/write verification failed.")
        mock_cache.delete.assert_called_once()

    def test_webhook_check_reports_warning_when_no_enabled_endpoints_exist(self):
        result = HealthcheckService.run_webhook_check()

        self.assertEqual(result.status, "warning")
        self.assertEqual(result.message, "No enabled webhook endpoints are configured.")

    @patch("djangoapp.healthchecks.checks.request.urlopen")
    def test_webhook_check_reports_healthy_when_enabled_endpoints_are_reachable(self, mock_urlopen):
        mock_response = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        WebhookEndpoint.objects.create(
            name="Primary endpoint",
            target_url="https://example.com/webhooks/primary",
            enabled=True,
        )

        result = HealthcheckService.run_webhook_check()

        self.assertEqual(result.status, "healthy")
        self.assertEqual(result.message, "1 enabled webhook endpoint reachable.")

    @patch("djangoapp.healthchecks.checks.request.urlopen")
    def test_webhook_check_reports_unhealthy_when_enabled_endpoint_is_unreachable(self, mock_urlopen):
        mock_urlopen.side_effect = error.URLError("connection refused")
        WebhookEndpoint.objects.create(
            name="Primary endpoint",
            target_url="https://example.com/webhooks/primary",
            enabled=True,
        )

        result = HealthcheckService.run_webhook_check()

        self.assertEqual(result.status, "unhealthy")
        self.assertEqual(result.message, "Webhook endpoints unreachable: Primary endpoint.")

    @patch("djangoapp.healthchecks.checks.request.urlopen")
    def test_webhook_check_treats_http_response_errors_as_reachable(self, mock_urlopen):
        mock_urlopen.side_effect = error.HTTPError(
            "https://example.com/webhooks/primary",
            405,
            "method not allowed",
            hdrs=None,
            fp=None,
        )
        WebhookEndpoint.objects.create(
            name="Primary endpoint",
            target_url="https://example.com/webhooks/primary",
            enabled=True,
        )

        result = HealthcheckService.run_webhook_check()

        self.assertEqual(result.status, "healthy")
        self.assertEqual(result.message, "1 enabled webhook endpoint reachable.")
