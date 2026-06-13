from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .workflow_state import WorkflowState


class WorkflowStateAutoAssignmentRule(models.Model):
    workflow_state = models.CharField(
        max_length=24,
        choices=WorkflowState.choices,
        unique=True,
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        related_name="workflow_state_auto_assignment_rules",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="workflow_state_auto_assignment_rules",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["workflow_state"]
        verbose_name = _("Workflow state auto-assignment rule")
        verbose_name_plural = _("Workflow state auto-assignment rules")

    def __str__(self):
        return self.get_workflow_state_display()

    def clean(self):
        super().clean()

        if not self.user:
            return

        if self.user.groups.filter(pk=self.group_id).exists():
            return

        raise ValidationError({
            "user": _("The configured user must belong to the configured group."),
        })
