from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from .issue_priority import IssuePriority
from .workflow_state import WorkflowState


def _missing_group_for_user(issue):
    return bool(issue.user and not issue.group)


def _user_not_in_group(issue):
    return bool(issue.group and issue.user and not issue.user.groups.filter(pk=issue.group_id).exists())


def _missing_archive_timestamp(issue):
    return bool(issue.archived_by_user and not issue.archived_at)


class Issue(models.Model):
    issue_number = models.CharField(max_length=32, unique=True, blank=True)
    collection = models.ForeignKey(
        "core.Collection",
        on_delete=models.PROTECT,
        related_name="issues",
    )
    collection_issue_sequence = models.PositiveIntegerField(null=True, blank=True, editable=False)
    title = models.CharField(max_length=255)
    description_markdown = models.TextField(blank=True)
    category = models.ForeignKey(
        "core.IssueCategory",
        on_delete=models.PROTECT,
        related_name="issues",
    )
    priority = models.CharField(
        max_length=16,
        choices=IssuePriority.choices,
        default=IssuePriority.MEDIUM,
    )
    workflow_state = models.CharField(
        max_length=24,
        choices=WorkflowState.choices,
        default=WorkflowState.BACKLOG,
    )
    board_position = models.PositiveIntegerField(default=0, editable=False)
    group = models.ForeignKey(
        "auth.Group",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="dispatched_issues",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="assigned_issues",
    )
    is_escalated = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="archived_issues",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.issue_number or self.title

    @property
    def is_archived(self):
        return self.archived_at is not None

    def clean(self):
        super().clean()
        self._validate_assignment()
        self._validate_archive_state()

    def _validate_assignment(self):
        if _missing_group_for_user(self):
            raise ValidationError({"group": _("A group is required when a user is assigned.")})

        if _user_not_in_group(self):
            raise ValidationError({"user": _("The assigned user must belong to the assigned group.")})

    def _validate_archive_state(self):
        if _missing_archive_timestamp(self):
            raise ValidationError({"archived_at": _("Archived timestamp is required when archived by user is set.")})

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.board_position < 1:
            self.board_position = self._get_next_board_position()

        if self.pk is not None or self.issue_number:
            super().save(*args, **kwargs)
            return

        update_fields = kwargs.get("update_fields")

        with transaction.atomic():
            collection = self.collection.__class__.objects.select_for_update().get(pk=self.collection_id)
            self.collection = collection
            self.collection_issue_sequence = collection.next_issue_sequence
            self.issue_number = self._build_issue_number()
            collection.next_issue_sequence += 1
            collection.save(update_fields=["next_issue_sequence"])
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {
                    "board_position",
                    "issue_number",
                    "collection_issue_sequence",
                }
            super().save(*args, **kwargs)

    def _build_issue_number(self):
        return f"{self.collection.prefix}-{self.collection_issue_sequence:03d}"

    def _get_next_board_position(self):
        current_max = (
            self.__class__.objects
            .filter(
                workflow_state=self.workflow_state,
                priority=self.priority,
            )
            .aggregate(max_position=Max("board_position"))
            .get("max_position")
            or 0
        )
        return current_max + 1
