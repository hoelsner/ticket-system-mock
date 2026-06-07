from django.db import models
from django.utils.translation import gettext_lazy as _


class WebhookDeliveryStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    SUCCESS = "success", _("Success")
    PARTIAL_FAILURE = "partial_failure", _("Partial failure")
    FAILED = "failed", _("Failed")
