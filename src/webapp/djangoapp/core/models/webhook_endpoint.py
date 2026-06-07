from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .webhook_delivery_status import WebhookDeliveryStatus
from .webhook_event_type import WebhookEventType


def _invalid_subscribed_event_types(subscribed_event_types):
    valid_event_types = {choice for choice, _label in WebhookEventType.choices}
    return [event_type for event_type in subscribed_event_types if event_type not in valid_event_types]


class WebhookEndpoint(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    target_url = models.URLField()
    enabled = models.BooleanField(default=True)
    subscribed_event_types = models.JSONField(default=list, blank=True)
    secret = models.CharField(max_length=255, blank=True)
    timeout_seconds = models.PositiveIntegerField(default=5)
    max_retries = models.PositiveIntegerField(default=3)
    retry_backoff_seconds = models.PositiveIntegerField(default=60)
    last_delivery_status = models.CharField(
        max_length=32,
        choices=WebhookDeliveryStatus.choices,
        blank=True,
    )
    last_delivery_attempt_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if not isinstance(self.subscribed_event_types, list):
            raise ValidationError({"subscribed_event_types": _("Subscribed event types must be a list.")})

        invalid_event_types = _invalid_subscribed_event_types(self.subscribed_event_types)
        if invalid_event_types:
            raise ValidationError({
                "subscribed_event_types": _("Unsupported event types: %(event_types)s")
                % {
                    "event_types": ", ".join(invalid_event_types),
                }
            })

        self.subscribed_event_types = list(dict.fromkeys(self.subscribed_event_types))

    def is_subscribed_to(self, event_type):
        return self.enabled and event_type in self.subscribed_event_types

    @property
    def subscribed_event_types_display(self):
        return ", ".join(self.subscribed_event_types)
