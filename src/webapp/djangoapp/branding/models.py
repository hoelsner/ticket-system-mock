from django.core.validators import RegexValidator
from django.db import models

HEX_COLOR_VALIDATOR = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Use a hex color in the format #RRGGBB.",
)


def theme_color_field(*, default, help_text):
    return models.CharField(
        max_length=7,
        default=default,
        validators=[HEX_COLOR_VALIDATOR],
        help_text=help_text,
    )


def branding_logo_upload_to(instance, filename):
    return f"branding/logo/{filename}"


def branding_login_background_upload_to(instance, filename):
    return f"branding/login-background/{filename}"


LOGIN_MESSAGE_LEVEL_CHOICES = (
    ("info", "Info"),
    ("success", "Success"),
    ("warning", "Warning"),
    ("error", "Error"),
)


class AppBranding(models.Model):
    singleton_enforcer = models.CharField(max_length=32, default="app-branding", unique=True, editable=False)
    display_name_override = models.CharField(max_length=255, blank=True)
    logo_image = models.FileField(upload_to=branding_logo_upload_to, blank=True)
    login_background_image = models.FileField(upload_to=branding_login_background_upload_to, blank=True)
    login_message_text = models.TextField(
        blank=True,
        verbose_name="Login screen message",
        help_text="Optional message shown above the sign-in form.",
    )
    login_message_level = models.CharField(
        max_length=20,
        choices=LOGIN_MESSAGE_LEVEL_CHOICES,
        default="info",
        verbose_name="Login message style",
        help_text="Visual style for the login screen message.",
    )
    light_primary_color = theme_color_field(
        default="#0172ad",
        help_text="Primary accent color for light mode.",
    )
    light_primary_hover_color = theme_color_field(
        default="#015887",
        help_text="Primary hover accent color for light mode.",
    )
    dark_primary_color = theme_color_field(
        default="#01aaff",
        help_text="Primary accent color for dark mode.",
    )
    dark_primary_hover_color = theme_color_field(
        default="#79c0ff",
        help_text="Primary hover accent color for dark mode.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "App branding"
        verbose_name_plural = "App branding"

    def save(self, *args, **kwargs):
        self.singleton_enforcer = "app-branding"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name_override or "App branding"
