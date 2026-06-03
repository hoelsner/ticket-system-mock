import base64
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from djangoapp.rest_api.api import DjangoBasicAuth, current_user, health


class RestApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="demo",
            password="demo-password-123",
        )

    def basic_auth_header(self, username="demo", password="demo-password-123"):
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}

    def test_api_requires_http_basic_auth(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 401)

    def test_api_rejects_invalid_http_basic_auth_credentials(self):
        response = self.client.get(
            "/api/health",
            headers=self.basic_auth_header(password="wrong-password"),
        )

        self.assertEqual(response.status_code, 401)

    def test_api_health_returns_ok_with_http_basic_auth(self):
        response = self.client.get(
            "/api/health",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_api_accepts_http_basic_auth(self):
        response = self.client.get(
            "/api/auth/me",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "demo")

    def test_basic_auth_backend_returns_active_user(self):
        backend = DjangoBasicAuth()

        with patch("djangoapp.rest_api.api.authenticate", return_value=self.user):
            authenticated = backend.authenticate(
                request=None,
                username="demo",
                password="demo-password-123",
            )

        self.assertEqual(authenticated, self.user)

    def test_basic_auth_backend_rejects_inactive_or_missing_user(self):
        backend = DjangoBasicAuth()

        with patch("djangoapp.rest_api.api.authenticate", return_value=None):
            authenticated = backend.authenticate(
                request=None,
                username="demo",
                password="wrong-password",
            )

        self.assertIsNone(authenticated)

    def test_health_endpoint_returns_ok_payload(self):
        self.assertEqual(health(request=None), {"status": "ok"})

    def test_current_user_endpoint_serializes_authenticated_user(self):
        request = SimpleNamespace(auth=self.user)

        payload = current_user(request)

        self.assertEqual(payload["username"], "demo")
        self.assertFalse(payload["is_staff"])
        self.assertFalse(payload["is_superuser"])
