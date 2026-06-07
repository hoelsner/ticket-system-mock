from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from djangoapp.healthchecks.checks import HealthCheckResult, HealthCheckSummary


class HealthcheckApiTests(TestCase):
    @patch("djangoapp.healthchecks.views.HealthcheckService.run_all_checks")
    def test_api_returns_healthy_response(self, mock_run_all_checks):
        mock_run_all_checks.return_value = HealthCheckSummary(
            status="healthy",
            duration_ms=18,
            checks={
                "database": HealthCheckResult(name="database", status="healthy", duration_ms=4),
                "migrations": HealthCheckResult(name="migrations", status="healthy", duration_ms=9),
                "cache": HealthCheckResult(name="cache", status="healthy", duration_ms=5),
                "webhooks": HealthCheckResult(name="webhooks", status="healthy", duration_ms=3),
            },
        )

        response = self.client.get(reverse("healthcheck-api"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
        self.assertEqual(response.json()["duration_ms"], 18)
        self.assertEqual(sorted(response.json()["checks"].keys()), ["cache", "database", "migrations", "webhooks"])

    @patch("djangoapp.healthchecks.views.HealthcheckService.run_all_checks")
    def test_api_returns_unhealthy_response_and_logs_failure(self, mock_run_all_checks):
        mock_run_all_checks.return_value = HealthCheckSummary(
            status="unhealthy",
            duration_ms=27,
            checks={
                "database": HealthCheckResult(name="database", status="healthy", duration_ms=4),
                "migrations": HealthCheckResult(
                    name="migrations",
                    status="unhealthy",
                    duration_ms=18,
                    message="Pending migrations detected.",
                ),
                "cache": HealthCheckResult(name="cache", status="healthy", duration_ms=5),
                "webhooks": HealthCheckResult(name="webhooks", status="healthy", duration_ms=3),
            },
        )

        with self.assertLogs("djangoapp.healthchecks.views", level="WARNING") as captured_logs:
            response = self.client.get(reverse("healthcheck-api"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "unhealthy")
        self.assertEqual(response.json()["checks"]["migrations"]["message"], "Pending migrations detected.")
        self.assertNotIn("exception_type", response.json()["checks"]["migrations"])
        self.assertIn("healthcheck failed", captured_logs.output[0])

    @patch("djangoapp.healthchecks.views.HealthcheckService.run_all_checks")
    def test_api_returns_warning_response_without_service_failure(self, mock_run_all_checks):
        mock_run_all_checks.return_value = HealthCheckSummary(
            status="warning",
            duration_ms=14,
            checks={
                "database": HealthCheckResult(name="database", status="healthy", duration_ms=4),
                "migrations": HealthCheckResult(name="migrations", status="healthy", duration_ms=3),
                "cache": HealthCheckResult(name="cache", status="healthy", duration_ms=2),
                "webhooks": HealthCheckResult(
                    name="webhooks",
                    status="warning",
                    duration_ms=5,
                    message="No enabled webhook endpoints are configured.",
                ),
            },
        )

        with self.assertLogs("djangoapp.healthchecks.views", level="WARNING") as captured_logs:
            response = self.client.get(reverse("healthcheck-api"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "warning")
        self.assertEqual(
            response.json()["checks"]["webhooks"]["message"], "No enabled webhook endpoints are configured."
        )
        self.assertIn("healthcheck failed", captured_logs.output[0])

    @patch("djangoapp.healthchecks.views.HealthcheckService.run_all_checks")
    def test_api_logs_errors_for_exception_backed_failures(self, mock_run_all_checks):
        mock_run_all_checks.return_value = HealthCheckSummary(
            status="unhealthy",
            duration_ms=31,
            checks={
                "database": HealthCheckResult(
                    name="database",
                    status="unhealthy",
                    duration_ms=31,
                    message="Database connectivity check failed.",
                    exception_type="RuntimeError",
                )
            },
        )

        with self.assertLogs("djangoapp.healthchecks.views", level="ERROR") as captured_logs:
            response = self.client.get(reverse("healthcheck-api"))

        self.assertEqual(response.status_code, 503)
        self.assertIn("exception_type=RuntimeError", captured_logs.output[0])
