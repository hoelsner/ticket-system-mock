from django.contrib import admin
from django.contrib.admin.helpers import AdminReadonlyField
from django.utils.html import format_html

from .models import AppBranding

if not hasattr(AdminReadonlyField, "is_fieldset"):
    setattr(AdminReadonlyField, "is_fieldset", False)


@admin.register(AppBranding)
class AppBrandingAdmin(admin.ModelAdmin):
    list_display = ("display_name_override", "logo_preview", "login_background_preview", "updated_at")
    readonly_fields = ("created_at", "updated_at", "logo_preview", "login_background_preview")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "display_name_override",
                    "logo_image",
                    "logo_preview",
                    "login_background_image",
                    "login_background_preview",
                )
            },
        ),
        (
            "Login screen",
            {"fields": ("login_message_text", "login_message_level")},
        ),
        (
            "Light mode theme",
            {"fields": ("light_primary_color", "light_primary_hover_color")},
        ),
        (
            "Dark mode theme",
            {"fields": ("dark_primary_color", "dark_primary_hover_color")},
        ),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at")},
        ),
    )

    def has_add_permission(self, request):
        return not AppBranding.objects.exists()

    @admin.display(description="Logo preview")
    def logo_preview(self, obj):
        if not obj or not obj.logo_image:
            return "Using the default placeholder logo."
        return format_html(
            '<img src="{}" alt="Current logo" style="max-height: 3rem; width: auto; border-radius: 0.35rem;" />',
            obj.logo_image.url,
        )

    @admin.display(description="Login background preview")
    def login_background_preview(self, obj):
        if not obj or not obj.login_background_image:
            return "Using the default placeholder login background image."
        return format_html(
            '<img src="{}" alt="Current login background" style="max-width: 14rem; width: 100%; height: auto; border-radius: 0.5rem;" />',
            obj.login_background_image.url,
        )
