from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from djangoapp.healthchecks.checks import HealthCheckResult, HealthCheckSummary


class HealthcheckFrontendTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="health-user",
            password="demo-password-123",
        )

    def test_status_page_redirects_anonymous_users_to_login(self):
        response = self.client.get(reverse("healthcheck-status"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.headers["Location"])

    @patch("djangoapp.healthchecks.views.HealthcheckService.run_all_checks")
    @patch("djangoapp.healthchecks.views.HealthcheckService.run_check")
    def test_status_page_renders_shell_without_running_checks(self, mock_run_check, mock_run_all_checks):
        self.client.force_login(self.user)

        response = self.client.get(reverse("healthcheck-status"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Service Health")
        self.assertContains(response, "Checking")
        self.assertContains(response, "lib/htmx/htmx.min.js")
        self.assertContains(response, reverse("healthcheck-status-summary"))
        self.assertContains(response, reverse("healthcheck-status-check", kwargs={"check_name": "database"}))
        self.assertContains(response, reverse("healthcheck-status-check", kwargs={"check_name": "webhooks"}))
        self.assertContains(response, 'hx-trigger="load"')
        self.assertContains(response, 'hx-trigger="healthcheck:run-summary from:body"')
        self.assertContains(response, 'hx-trigger="healthcheck:run-migrations from:body"')
        self.assertContains(response, 'hx-trigger="healthcheck:run-cache from:body"')
        self.assertContains(response, 'hx-trigger="healthcheck:run-webhooks from:body"')
        self.assertContains(response, "Each healthcheck runs one-by-one")
        self.assertContains(response, "healthcheck-card--checking")
        self.assertNotContains(response, 'http-equiv="refresh"')
        mock_run_all_checks.assert_not_called()
        mock_run_check.assert_not_called()

    @patch("djangoapp.healthchecks.views.HealthcheckService.run_all_checks")
    def test_summary_partial_returns_health_fragment(self, mock_run_all_checks):
        self.client.force_login(self.user)
        mock_run_all_checks.return_value = HealthCheckSummary(
            status="healthy",
            duration_ms=22,
            checks={
                "database": HealthCheckResult(name="database", status="healthy", duration_ms=4),
                "migrations": HealthCheckResult(name="migrations", status="healthy", duration_ms=8),
                "cache": HealthCheckResult(name="cache", status="healthy", duration_ms=10),
                "webhooks": HealthCheckResult(name="webhooks", status="warning", duration_ms=5),
            },
        )

        response = self.client.get(reverse("healthcheck-status-summary"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Overall status")
        self.assertContains(response, "Healthy")
        self.assertContains(response, "22 ms")
        self.assertContains(response, "healthcheck-card--healthy")

    @patch("djangoapp.healthchecks.views.HealthcheckService.run_check")
    def test_check_partial_returns_individual_fragment(self, mock_run_check):
        self.client.force_login(self.user)
        mock_run_check.return_value = HealthCheckResult(
            name="database",
            status="unhealthy",
            duration_ms=7,
            message="Database connectivity check failed.",
        )

        response = self.client.get(reverse("healthcheck-status-check", kwargs={"check_name": "database"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Database")
        self.assertContains(response, "Unhealthy")
        self.assertContains(response, "7 ms")
        self.assertContains(response, "Database connectivity check failed.")
        self.assertContains(response, "healthcheck-card--unhealthy")
        self.assertEqual(response.headers["HX-Trigger"], "healthcheck:run-migrations")

    @patch("djangoapp.healthchecks.views.HealthcheckService.run_check")
    def test_webhook_check_partial_returns_warning_fragment(self, mock_run_check):
        self.client.force_login(self.user)
        mock_run_check.return_value = HealthCheckResult(
            name="webhooks",
            status="warning",
            duration_ms=6,
            message="No enabled webhook endpoints are configured.",
        )

        response = self.client.get(reverse("healthcheck-status-check", kwargs={"check_name": "webhooks"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Webhook endpoints")
        self.assertContains(response, "Warning")
        self.assertContains(response, "healthcheck-card--warning")
        self.assertEqual(response.headers["HX-Trigger"], "healthcheck:run-summary")

    @patch("djangoapp.healthchecks.views.HealthcheckService.run_check")
    def test_cache_check_partial_triggers_webhook_check(self, mock_run_check):
        self.client.force_login(self.user)
        mock_run_check.return_value = HealthCheckResult(
            name="cache",
            status="healthy",
            duration_ms=5,
        )

        response = self.client.get(reverse("healthcheck-status-check", kwargs={"check_name": "cache"}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["HX-Trigger"], "healthcheck:run-webhooks")
