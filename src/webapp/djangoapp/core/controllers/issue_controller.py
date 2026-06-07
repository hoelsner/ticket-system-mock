from django.db import transaction
from django.utils import timezone

from djangoapp.core.models import Issue, IssueStateTransition, WorkflowState

from .webhook_controller import WebhookController


class IssueController:
    @staticmethod
    def touch(issue):
        issue.save(update_fields=["updated_at"])
        return issue

    @staticmethod
    @transaction.atomic
    def move_on_board(issue, to_state, changed_by_user, position_index=0, reason=""):
        previous_state = issue.workflow_state
        previous_priority = issue.priority

        issue, transition = IssueController.update_workflow_state(
            issue,
            to_state,
            changed_by_user,
            reason=reason,
        )

        if previous_state != issue.workflow_state:
            IssueController._normalize_band(previous_state, previous_priority, exclude_issue_id=issue.pk)

        IssueController._insert_into_band(issue, position_index)
        return issue, transition

    @staticmethod
    @transaction.atomic
    def archive(issue, archived_by_user):
        previous_state = issue.workflow_state
        previous_priority = issue.priority
        issue.archived_at = timezone.now()
        issue.archived_by_user = archived_by_user
        issue.save(update_fields=["archived_at", "archived_by_user", "updated_at"])
        IssueController._normalize_band(previous_state, previous_priority, exclude_issue_id=issue.pk)
        return issue

    @staticmethod
    @transaction.atomic
    def update_workflow_state(issue, to_state, changed_by_user, reason=""):
        from_state = issue.workflow_state

        if from_state == to_state:
            return issue, None

        issue.workflow_state = to_state

        now = timezone.now()
        if to_state == WorkflowState.RESOLVED:
            issue.resolved_at = now
        elif to_state == WorkflowState.CLOSED:
            issue.closed_at = now

        issue.save()

        transition = IssueStateTransition.objects.create(
            issue=issue,
            from_state=from_state,
            to_state=to_state,
            changed_by_user=changed_by_user,
            reason=reason,
        )
        if to_state == WorkflowState.CLOSED:
            WebhookController.create_issue_closed_event(
                issue,
                actor=changed_by_user,
                transition=transition,
            )
        return issue, transition

    @staticmethod
    @transaction.atomic
    def sync_board_position(issue, previous_state, previous_priority):
        band_changed = previous_state != issue.workflow_state or previous_priority != issue.priority
        if not band_changed:
            if issue.board_position < 1:
                IssueController._insert_into_band(issue, 0)
            return issue

        IssueController._normalize_band(previous_state, previous_priority, exclude_issue_id=issue.pk)
        issue.board_position = 0
        IssueController._insert_into_band(issue, None)
        return issue

    @staticmethod
    def _insert_into_band(issue, position_index):
        siblings = list(
            Issue.objects
            .filter(
                archived_at__isnull=True,
                workflow_state=issue.workflow_state,
                priority=issue.priority,
            )
            .exclude(pk=issue.pk)
            .order_by("board_position", "created_at", "pk")
        )
        clamped_index = len(siblings) if position_index is None else max(0, min(position_index, len(siblings)))
        siblings.insert(clamped_index, issue)

        for index, sibling in enumerate(siblings, start=1):
            if sibling.pk == issue.pk:
                if issue.board_position != index:
                    issue.board_position = index
                    issue.save(update_fields=["board_position", "updated_at"])
                continue

            if sibling.board_position != index:
                sibling.board_position = index
                sibling.save(update_fields=["board_position", "updated_at"])

    @staticmethod
    def _normalize_band(workflow_state, priority, exclude_issue_id=None):
        queryset = Issue.objects.filter(
            archived_at__isnull=True,
            workflow_state=workflow_state,
            priority=priority,
        )
        if exclude_issue_id is not None:
            queryset = queryset.exclude(pk=exclude_issue_id)

        for index, sibling in enumerate(queryset.order_by("board_position", "created_at", "pk"), start=1):
            if sibling.board_position != index:
                sibling.board_position = index
                sibling.save(update_fields=["board_position", "updated_at"])
