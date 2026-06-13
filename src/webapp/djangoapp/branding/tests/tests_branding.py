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
        self.assertEqual(snapshot.login_message_text, "")
        self.assertEqual(snapshot.login_message_level, "info")
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
            login_message_text="Planned maintenance starts at 18:00 UTC.",
            login_message_level="warning",
            light_primary_color="#1357aa",
            light_primary_hover_color="#0f4b92",
            dark_primary_color="#4db6ff",
            dark_primary_hover_color="#93d3ff",
        )

        response = self.client.get(reverse("login"))

        self.assertContains(response, "Operations Control")
        self.assertContains(response, branding.logo_image.url)
        self.assertContains(response, branding.login_background_image.url)
        self.assertContains(response, "Planned maintenance starts at 18:00 UTC.")
        self.assertContains(response, "message-panel__item--warning")
        self.assertContains(response, "--pico-primary: #1357aa;")
        self.assertContains(response, "--pico-primary-hover: #0f4b92;")
        self.assertContains(response, "--pico-primary: #4db6ff;")
        self.assertContains(response, "--pico-primary-hover: #93d3ff;")

    def test_branding_admin_exposes_login_message_fields(self):
        admin_user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin-password-123",
        )
        branding = AppBranding.objects.create()
        self.client.force_login(admin_user)

        response = self.client.get(reverse("admin:branding_appbranding_change", args=[branding.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login screen")
        self.assertContains(response, "Login screen message")
        self.assertContains(response, "Login message style")

    def test_branding_admin_change_page_renders_without_template_debug_noise(self):
        admin_user = get_user_model().objects.create_superuser(
            username="admin-no-debug",
            email="admin-no-debug@example.com",
            password="admin-password-123",
        )
        branding = AppBranding.objects.create()
        self.client.force_login(admin_user)

        with self.assertNoLogs("django.template", level="DEBUG"):
            response = self.client.get(reverse("admin:branding_appbranding_change", args=[branding.pk]))

        self.assertEqual(response.status_code, 200)

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
