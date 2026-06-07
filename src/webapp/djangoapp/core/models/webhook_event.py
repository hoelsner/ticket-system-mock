import uuid

from django.db import models
from django.utils import timezone

from .webhook_delivery_status import WebhookDeliveryStatus
from .webhook_event_type import WebhookEventType


class WebhookEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=64, choices=WebhookEventType.choices)
    issue = models.ForeignKey(
        "core.Issue",
        on_delete=models.CASCADE,
        related_name="webhook_events",
    )
    target_endpoint_ids = models.JSONField(default=list, blank=True)
    payload = models.JSONField(default=dict)
    occurred_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_status = models.CharField(
        max_length=32,
        choices=WebhookDeliveryStatus.choices,
        default=WebhookDeliveryStatus.PENDING,
    )

    class Meta:
        ordering = ["-occurred_at", "-created_at"]

    def __str__(self):
        return f"{self.event_type} for {self.issue}"
