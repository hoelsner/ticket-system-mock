from django.apps import AppConfig


class UserInterfaceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "djangoapp.user_interface"

    def ready(self):
        from . import signals  # noqa: F401
