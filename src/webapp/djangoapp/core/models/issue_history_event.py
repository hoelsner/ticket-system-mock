from django.conf import settings
from django.db import models
from django.utils import timezone


class IssueHistoryEvent(models.Model):
    FIELD_CHANGED = "FIELD_CHANGED"
    ATTACHMENT_ADDED = "ATTACHMENT_ADDED"
    ATTACHMENT_UPDATED = "ATTACHMENT_UPDATED"
    ATTACHMENT_REMOVED = "ATTACHMENT_REMOVED"

    EVENT_TYPE_CHOICES = (
        (FIELD_CHANGED, "Field changed"),
        (ATTACHMENT_ADDED, "Attachment added"),
        (ATTACHMENT_UPDATED, "Attachment updated"),
        (ATTACHMENT_REMOVED, "Attachment removed"),
    )

    issue = models.ForeignKey(
        "core.Issue",
        on_delete=models.CASCADE,
        related_name="history_events",
    )
    event_type = models.CharField(max_length=32, choices=EVENT_TYPE_CHOICES)
    field_name = models.CharField(max_length=32, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="issue_history_events",
    )
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-changed_at", "-pk"]

    def __str__(self):
        return f"{self.issue} {self.event_type}"
