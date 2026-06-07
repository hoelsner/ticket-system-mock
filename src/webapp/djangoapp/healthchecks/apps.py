from django.apps import AppConfig


class HealthchecksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "djangoapp.healthchecks"
    verbose_name = "Healthchecks"
