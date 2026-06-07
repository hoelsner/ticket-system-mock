from django.db import models
from django.utils import timezone


class WebhookDeliveryAttempt(models.Model):
    webhook_endpoint = models.ForeignKey(
        "core.WebhookEndpoint",
        on_delete=models.CASCADE,
        related_name="delivery_attempts",
    )
    webhook_event = models.ForeignKey(
        "core.WebhookEvent",
        on_delete=models.CASCADE,
        related_name="delivery_attempts",
    )
    attempt_number = models.PositiveIntegerField()
    request_headers = models.JSONField(default=dict, blank=True)
    request_body = models.TextField(blank=True)
    response_status_code = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    attempted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-attempted_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["webhook_endpoint", "webhook_event", "attempt_number"],
                name="core_webhook_attempt_unique_number",
            )
        ]

    def __str__(self):
        return f"Attempt {self.attempt_number} for {self.webhook_event}"
