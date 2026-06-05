from django.conf import settings
from django.db import models
from django.utils import timezone

from .workflow_state import WorkflowState


class IssueStateTransition(models.Model):
    issue = models.ForeignKey(
        "core.Issue",
        on_delete=models.CASCADE,
        related_name="state_transitions",
    )
    from_state = models.CharField(max_length=24, choices=WorkflowState.choices)
    to_state = models.CharField(max_length=24, choices=WorkflowState.choices)
    changed_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="issue_state_transitions",
    )
    changed_at = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.issue} {self.from_state}->{self.to_state}"