from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from djangoapp.healthchecks.checks import HealthCheckResult, HealthCheckSummary
from djangoapp.healthchecks.views import _next_check_event, _response_status


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
    @patch("djangoapp.healthchecks.views.HealthcheckService.run_check")
    def test_status_page_renders_without_template_debug_noise(self, mock_run_check, mock_run_all_checks):
        self.client.force_login(self.user)

        with self.assertNoLogs("django.template", level="DEBUG"):
            response = self.client.get(reverse("healthcheck-status"))

        self.assertEqual(response.status_code, 200)
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

    @patch("djangoapp.healthchecks.views.HealthcheckService.run_all_checks")
    def test_summary_partial_logs_unhealthy_results(self, mock_run_all_checks):
        self.client.force_login(self.user)
        mock_run_all_checks.return_value = HealthCheckSummary(
            status="warning",
            duration_ms=22,
            checks={
                "webhooks": HealthCheckResult(
                    name="webhooks",
                    status="warning",
                    duration_ms=5,
                    message="No enabled webhook endpoints are configured.",
                )
            },
        )

        with self.assertLogs("djangoapp.healthchecks.views", level="WARNING") as captured_logs:
            response = self.client.get(reverse("healthcheck-status-summary"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("healthcheck failed", captured_logs.output[0])

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

    @patch("djangoapp.healthchecks.views._next_check_event", return_value=None)
    @patch("djangoapp.healthchecks.views.HealthcheckService.run_check")
    def test_check_partial_omits_hx_trigger_when_no_follow_up_event(self, mock_run_check, _mock_next_check_event):
        self.client.force_login(self.user)
        mock_run_check.return_value = HealthCheckResult(
            name="database",
            status="healthy",
            duration_ms=5,
        )

        response = self.client.get(reverse("healthcheck-status-check", kwargs={"check_name": "database"}))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("HX-Trigger", response.headers)

    def test_check_partial_returns_404_for_unknown_check(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("healthcheck-status-check", kwargs={"check_name": "unknown"}))

        self.assertEqual(response.status_code, 404)

    def test_response_status_returns_expected_http_codes(self):
        self.assertEqual(_response_status(HealthCheckSummary(status="healthy", duration_ms=1, checks={})), 200)
        self.assertEqual(_response_status(HealthCheckSummary(status="warning", duration_ms=1, checks={})), 200)
        self.assertEqual(_response_status(HealthCheckSummary(status="unhealthy", duration_ms=1, checks={})), 503)

    def test_next_check_event_handles_invalid_and_final_check_names(self):
        self.assertIsNone(_next_check_event("unknown"))
        self.assertEqual(_next_check_event("webhooks"), "healthcheck:run-summary")
