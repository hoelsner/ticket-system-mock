from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "language_preference", "avatar_type", "is_system_user", "updated_at")
    list_filter = ("language_preference", "avatar_type", "is_system_user")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("user",)}),
        (
            "Preferences",
            {
                "fields": (
                    "language_preference",
                    "avatar_type",
                    "is_system_user",
                    "avatar_image",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
