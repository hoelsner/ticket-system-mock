from unittest.mock import MagicMock, patch
from urllib import error

from django.test import TestCase
from djangoapp.core.models import WebhookEndpoint
from djangoapp.healthchecks.checks import HealthCheckResult, HealthcheckService, HealthCheckSummary


class HealthcheckServiceTests(TestCase):
    def test_health_check_result_to_dict_omits_empty_message(self):
        result = HealthCheckResult(name="database", status="healthy", duration_ms=4)

        self.assertEqual(result.to_dict(), {"status": "healthy", "duration_ms": 4})

    def test_health_check_summary_to_dict_serializes_nested_results(self):
        summary = HealthCheckSummary(
            status="warning",
            duration_ms=12,
            checks={
                "webhooks": HealthCheckResult(
                    name="webhooks",
                    status="warning",
                    duration_ms=5,
                    message="No enabled webhook endpoints are configured.",
                )
            },
        )

        self.assertEqual(
            summary.to_dict(),
            {
                "status": "warning",
                "duration_ms": 12,
                "checks": {
                    "webhooks": {
                        "status": "warning",
                        "duration_ms": 5,
                        "message": "No enabled webhook endpoints are configured.",
                    }
                },
            },
        )

    @patch("djangoapp.healthchecks.checks.HealthcheckService.run_check")
    @patch("djangoapp.healthchecks.checks.HealthcheckService._duration_ms")
    def test_run_all_checks_returns_summary(self, mock_duration_ms, mock_run_check):
        mock_duration_ms.return_value = 9
        mock_run_check.side_effect = [
            HealthCheckResult(name="database", status="healthy", duration_ms=1),
            HealthCheckResult(name="migrations", status="healthy", duration_ms=2),
            HealthCheckResult(name="cache", status="healthy", duration_ms=3),
            HealthCheckResult(name="webhooks", status="warning", duration_ms=4, message="warn"),
        ]

        summary = HealthcheckService.run_all_checks()

        self.assertEqual(summary.status, "warning")
        self.assertEqual(summary.duration_ms, 9)
        self.assertEqual(list(summary.checks.keys()), list(HealthcheckService.CHECK_NAMES))

    @patch("djangoapp.healthchecks.checks.HealthcheckService.run_database_check")
    @patch("djangoapp.healthchecks.checks.HealthcheckService.run_migration_check")
    @patch("djangoapp.healthchecks.checks.HealthcheckService.run_cache_check")
    @patch("djangoapp.healthchecks.checks.HealthcheckService.run_webhook_check")
    def test_run_check_dispatches_by_name(
        self,
        mock_run_webhook_check,
        mock_run_cache_check,
        mock_run_migration_check,
        mock_run_database_check,
    ):
        mock_run_database_check.return_value = HealthCheckResult(name="database", status="healthy", duration_ms=1)
        mock_run_migration_check.return_value = HealthCheckResult(name="migrations", status="healthy", duration_ms=1)
        mock_run_cache_check.return_value = HealthCheckResult(name="cache", status="healthy", duration_ms=1)
        mock_run_webhook_check.return_value = HealthCheckResult(name="webhooks", status="healthy", duration_ms=1)

        self.assertEqual(HealthcheckService.run_check("database").name, "database")
        self.assertEqual(HealthcheckService.run_check("migrations").name, "migrations")
        self.assertEqual(HealthcheckService.run_check("cache").name, "cache")
        self.assertEqual(HealthcheckService.run_check("webhooks").name, "webhooks")

    @patch("djangoapp.healthchecks.checks.connection.cursor")
    def test_database_check_returns_healthy_result(self, mock_cursor):
        mock_context = MagicMock()
        mock_cursor.return_value.__enter__.return_value = mock_context

        result = HealthcheckService.run_database_check()

        self.assertEqual(result.status, "healthy")
        mock_context.execute.assert_called_once_with("SELECT 1")
        mock_context.fetchone.assert_called_once_with()

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

    @patch("djangoapp.healthchecks.checks.MigrationExecutor")
    def test_migration_check_hides_sensitive_exception_details(self, mock_executor_class):
        mock_executor_class.side_effect = RuntimeError("password=secret")

        result = HealthcheckService.run_migration_check()

        self.assertEqual(result.status, "unhealthy")
        self.assertEqual(result.message, "Migration status check failed.")
        self.assertEqual(result.exception_type, "RuntimeError")

    @patch("djangoapp.healthchecks.checks.MigrationExecutor")
    def test_migration_check_returns_healthy_result_without_pending_migrations(self, mock_executor_class):
        mock_executor = mock_executor_class.return_value
        mock_executor.loader.graph.leaf_nodes.return_value = [("core", "0001_initial")]
        mock_executor.migration_plan.return_value = []

        result = HealthcheckService.run_migration_check()

        self.assertEqual(result.status, "healthy")

    @patch("djangoapp.healthchecks.checks.caches")
    def test_cache_check_reports_read_write_mismatch(self, mock_caches):
        mock_cache = MagicMock()
        mock_cache.get.return_value = "wrong-value"
        mock_caches.__getitem__.return_value = mock_cache

        result = HealthcheckService.run_cache_check()

        self.assertEqual(result.status, "unhealthy")
        self.assertEqual(result.message, "Cache read/write verification failed.")
        mock_cache.delete.assert_called_once()

    @patch("djangoapp.healthchecks.checks.caches")
    def test_cache_check_hides_sensitive_exception_details(self, mock_caches):
        mock_cache = MagicMock()
        mock_cache.set.side_effect = RuntimeError("password=secret")
        mock_caches.__getitem__.return_value = mock_cache

        result = HealthcheckService.run_cache_check()

        self.assertEqual(result.status, "unhealthy")
        self.assertEqual(result.message, "Cache connectivity check failed.")
        self.assertEqual(result.exception_type, "RuntimeError")
        mock_cache.delete.assert_called_once()

    @patch("djangoapp.healthchecks.checks.caches")
    def test_cache_check_ignores_delete_failures_after_successful_read(self, mock_caches):
        mock_cache = MagicMock()
        mock_cache.get.return_value = "expected-value"
        mock_cache.delete.side_effect = RuntimeError("delete failed")
        mock_caches.__getitem__.return_value = mock_cache

        with patch("djangoapp.healthchecks.checks.uuid.uuid4") as mock_uuid4:
            mock_uuid4.side_effect = ["cache-key", MagicMock(hex="expected-value")]

            result = HealthcheckService.run_cache_check()

        self.assertEqual(result.status, "healthy")

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
    def test_webhook_check_reports_healthy_plural_message_for_multiple_endpoints(self, mock_urlopen):
        mock_response = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        WebhookEndpoint.objects.create(
            name="Primary endpoint",
            target_url="https://example.com/webhooks/primary",
            enabled=True,
        )
        WebhookEndpoint.objects.create(
            name="Secondary endpoint",
            target_url="https://example.com/webhooks/secondary",
            enabled=True,
        )

        result = HealthcheckService.run_webhook_check()

        self.assertEqual(result.status, "healthy")
        self.assertEqual(result.message, "2 enabled webhook endpoints reachable.")

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
    def test_webhook_check_reports_all_unreachable_endpoint_names(self, mock_urlopen):
        mock_urlopen.side_effect = error.URLError("connection refused")
        WebhookEndpoint.objects.create(
            name="Primary endpoint",
            target_url="https://example.com/webhooks/primary",
            enabled=True,
        )
        WebhookEndpoint.objects.create(
            name="Secondary endpoint",
            target_url="https://example.com/webhooks/secondary",
            enabled=True,
        )

        result = HealthcheckService.run_webhook_check()

        self.assertEqual(result.status, "unhealthy")
        self.assertEqual(
            result.message,
            "Webhook endpoints unreachable: Primary endpoint, Secondary endpoint.",
        )

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

    def test_duration_ms_never_returns_negative_values(self):
        with patch("djangoapp.healthchecks.checks.time.perf_counter", return_value=9.0):
            self.assertEqual(HealthcheckService._duration_ms(10.0), 0)

    def test_overall_status_prefers_unhealthy_then_warning_then_healthy(self):
        unhealthy_summary = {
            "database": HealthCheckResult(name="database", status="unhealthy", duration_ms=1),
        }
        warning_summary = {
            "webhooks": HealthCheckResult(name="webhooks", status="warning", duration_ms=1),
        }
        healthy_summary = {
            "database": HealthCheckResult(name="database", status="healthy", duration_ms=1),
            "cache": HealthCheckResult(name="cache", status="healthy", duration_ms=1),
        }
        mixed_summary = {
            "database": HealthCheckResult(name="database", status="unknown", duration_ms=1),
        }

        self.assertEqual(HealthcheckService._overall_status(unhealthy_summary), "unhealthy")
        self.assertEqual(HealthcheckService._overall_status(warning_summary), "warning")
        self.assertEqual(HealthcheckService._overall_status(healthy_summary), "healthy")
        self.assertEqual(HealthcheckService._overall_status(mixed_summary), "warning")
