from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from djangoapp.branding.models import AppBranding
from djangoapp.branding.services import get_branding_snapshot


class BrandingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="demo",
            password="demo-password-123",
        )

    def test_branding_snapshot_uses_default_assets_when_not_configured(self):
        snapshot = get_branding_snapshot()

        self.assertEqual(snapshot.display_name, "Ticket System Mock")
        self.assertTrue(snapshot.logo_url.endswith("/static/img/default_app_logo.png"))
        self.assertTrue(snapshot.login_background_url.endswith("/static/img/default_app_hero_image.png"))
        self.assertEqual(snapshot.light_primary_color, "#0172ad")
        self.assertEqual(snapshot.light_primary_hover_color, "#015887")
        self.assertEqual(snapshot.dark_primary_color, "#01aaff")
        self.assertEqual(snapshot.dark_primary_hover_color, "#79c0ff")

    def test_login_page_uses_uploaded_branding_assets(self):
        branding = AppBranding.objects.create(
            display_name_override="Operations Control",
            logo_image=SimpleUploadedFile(
                "brand-logo.svg",
                b"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10'></svg>",
                content_type="image/svg+xml",
            ),
            login_background_image=SimpleUploadedFile(
                "login-background.png",
                b"placeholder-background",
                content_type="image/png",
            ),
            light_primary_color="#1357aa",
            light_primary_hover_color="#0f4b92",
            dark_primary_color="#4db6ff",
            dark_primary_hover_color="#93d3ff",
        )

        response = self.client.get(reverse("login"))

        self.assertContains(response, "Operations Control")
        self.assertContains(response, branding.logo_image.url)
        self.assertContains(response, branding.login_background_image.url)
        self.assertContains(response, "--pico-primary: #1357aa;")
        self.assertContains(response, "--pico-primary-hover: #0f4b92;")
        self.assertContains(response, "--pico-primary: #4db6ff;")
        self.assertContains(response, "--pico-primary-hover: #93d3ff;")

    def test_branding_snapshot_uses_runtime_theme_colors(self):
        AppBranding.objects.create(
            light_primary_color="#1357aa",
            light_primary_hover_color="#0f4b92",
            dark_primary_color="#4db6ff",
            dark_primary_hover_color="#93d3ff",
        )

        snapshot = get_branding_snapshot()

        self.assertEqual(snapshot.light_primary_color, "#1357aa")
        self.assertEqual(snapshot.light_primary_hover_color, "#0f4b92")
        self.assertEqual(snapshot.dark_primary_color, "#4db6ff")
        self.assertEqual(snapshot.dark_primary_hover_color, "#93d3ff")

    def test_authenticated_shell_renders_runtime_theme_colors(self):
        AppBranding.objects.create(
            light_primary_color="#1357aa",
            light_primary_hover_color="#0f4b92",
            dark_primary_color="#4db6ff",
            dark_primary_hover_color="#93d3ff",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "--pico-primary: #1357aa;")
        self.assertContains(response, "--pico-primary-hover: #0f4b92;")
        self.assertContains(response, "--pico-primary: #4db6ff;")
        self.assertContains(response, "--pico-primary-hover: #93d3ff;")

    def test_authenticated_shell_renders_default_branding_logo(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "default_app_logo.png")
