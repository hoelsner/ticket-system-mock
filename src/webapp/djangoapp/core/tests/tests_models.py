from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase

from djangoapp.core.controllers import IssueCommentController, IssueController
from djangoapp.core.models import (
    Collection,
    Issue,
    IssueAttachment,
    IssueCategory,
    IssueComment,
    IssueCommentMention,
    IssuePriority,
    IssueStateTransition,
    WorkflowState,
    issue_attachment_upload_to,
)


class CoreModelTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.group = Group.objects.create(name="Network Operations")
        self.assigned_user = self.user_model.objects.create_user(
            username="analyst",
            password="demo-password-123",
        )
        self.assigned_user.groups.add(self.group)
        self.other_user = self.user_model.objects.create_user(
            username="observer",
            password="demo-password-123",
        )
        self.category = IssueCategory.objects.create(
            name="Incident",
            code="INC",
        )
        self.collection = Collection.objects.get(prefix="TASK")

    def create_issue(self, **overrides):
        payload = {
            "title": "Switch outage",
            "description_markdown": "Primary switch unavailable.",
            "collection": self.collection,
            "category": self.category,
        }
        payload.update(overrides)
        return Issue.objects.create(**payload)

    def test_issue_generates_issue_number_on_create(self):
        issue = self.create_issue()

        self.assertEqual(issue.issue_number, "TASK-001")
        self.assertEqual(issue.collection_issue_sequence, 1)
        self.assertEqual(issue.workflow_state, WorkflowState.BACKLOG)
        self.assertEqual(issue.board_position, 1)
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.next_issue_sequence, 2)

    def test_issue_number_sequence_is_scoped_to_collection(self):
        second_collection = Collection.objects.create(name="Bug", prefix="BUG")

        first_task = self.create_issue(title="Primary")
        second_task = self.create_issue(title="Secondary")
        bug = self.create_issue(title="Bug report", collection=second_collection)

        self.assertEqual(first_task.issue_number, "TASK-001")
        self.assertEqual(second_task.issue_number, "TASK-002")
        self.assertEqual(bug.issue_number, "BUG-001")

    def test_collection_name_must_be_unique(self):
        duplicate_collection = Collection(
            name=self.collection.name,
            prefix="TASKCOPY",
        )

        with self.assertRaises(ValidationError) as error:
            duplicate_collection.full_clean()

        self.assertIn("name", error.exception.message_dict)

    def test_category_name_must_be_unique(self):
        duplicate_category = IssueCategory(
            name=self.category.name,
            code="INC-COPY",
        )

        with self.assertRaises(ValidationError) as error:
            duplicate_category.full_clean()

        self.assertIn("name", error.exception.message_dict)

    def test_issue_requires_assigned_user_to_belong_to_group(self):
        issue = Issue(
            title="Switch outage",
            collection=self.collection,
            category=self.category,
            group=self.group,
            user=self.other_user,
        )

        with self.assertRaises(ValidationError):
            issue.full_clean()

    def test_issue_requires_group_when_user_is_assigned(self):
        issue = Issue(
            title="Switch outage",
            collection=self.collection,
            category=self.category,
            user=self.assigned_user,
        )

        with self.assertRaises(ValidationError):
            issue.full_clean()

    def test_issue_requires_archived_timestamp_when_archived_by_user_is_set(self):
        issue = Issue(
            title="Switch outage",
            collection=self.collection,
            category=self.category,
            archived_by_user=self.assigned_user,
        )

        with self.assertRaises(ValidationError):
            issue.full_clean()

    def test_archive_sets_soft_delete_metadata(self):
        issue = self.create_issue()

        IssueController.archive(issue, self.assigned_user)
        issue.refresh_from_db()

        self.assertIsNotNone(issue.archived_at)
        self.assertEqual(issue.archived_by_user, self.assigned_user)
        self.assertTrue(issue.is_archived)

    def test_update_workflow_state_records_transition_and_resolution_time(self):
        issue = self.create_issue(group=self.group, user=self.assigned_user)

        updated_issue, transition = IssueController.update_workflow_state(
            issue,
            WorkflowState.RESOLVED,
            changed_by_user=self.assigned_user,
            reason="Work completed",
        )

        updated_issue.refresh_from_db()

        self.assertEqual(updated_issue.workflow_state, WorkflowState.RESOLVED)
        self.assertIsNotNone(updated_issue.resolved_at)
        self.assertIsInstance(transition, IssueStateTransition)
        self.assertEqual(transition.from_state, WorkflowState.BACKLOG)
        self.assertEqual(transition.to_state, WorkflowState.RESOLVED)
        self.assertEqual(transition.changed_by_user, self.assigned_user)

    def test_update_workflow_state_sets_closed_timestamp(self):
        issue = self.create_issue(group=self.group, user=self.assigned_user)

        updated_issue, transition = IssueController.update_workflow_state(
            issue,
            WorkflowState.CLOSED,
            changed_by_user=self.assigned_user,
        )

        updated_issue.refresh_from_db()

        self.assertEqual(updated_issue.workflow_state, WorkflowState.CLOSED)
        self.assertIsNotNone(updated_issue.closed_at)
        self.assertIsNotNone(transition)

    def test_update_workflow_state_is_noop_when_state_does_not_change(self):
        issue = self.create_issue()

        updated_issue, transition = IssueController.update_workflow_state(
            issue,
            WorkflowState.BACKLOG,
            changed_by_user=self.assigned_user,
        )

        self.assertEqual(updated_issue.pk, issue.pk)
        self.assertIsNone(transition)
        self.assertEqual(IssueStateTransition.objects.count(), 0)

    def test_move_on_board_reorders_within_same_priority_band(self):
        first_issue = self.create_issue(title="Primary switch outage")
        second_issue = self.create_issue(title="Secondary switch outage")
        third_issue = self.create_issue(title="Tertiary switch outage")

        moved_issue, _transition = IssueController.move_on_board(
            third_issue,
            WorkflowState.BACKLOG,
            changed_by_user=self.assigned_user,
            position_index=0,
            reason="Prioritize within backlog",
        )

        first_issue.refresh_from_db()
        second_issue.refresh_from_db()
        moved_issue.refresh_from_db()

        self.assertEqual(moved_issue.board_position, 1)
        self.assertEqual(first_issue.board_position, 2)
        self.assertEqual(second_issue.board_position, 3)

    def test_archive_reindexes_remaining_priority_band(self):
        first_issue = self.create_issue(title="Primary switch outage")
        second_issue = self.create_issue(title="Secondary switch outage")

        IssueController.archive(first_issue, self.assigned_user)
        second_issue.refresh_from_db()

        self.assertEqual(second_issue.board_position, 1)

    def test_sync_board_position_moves_issue_to_new_priority_band_end(self):
        existing_high_priority = self.create_issue(
            title="Existing high priority work",
            priority=IssuePriority.HIGH,
        )
        issue = self.create_issue(title="Escalated work")

        issue.priority = IssuePriority.HIGH
        issue.save()
        IssueController.sync_board_position(issue, WorkflowState.BACKLOG, IssuePriority.MEDIUM)

        existing_high_priority.refresh_from_db()
        issue.refresh_from_db()

        self.assertEqual(existing_high_priority.board_position, 1)
        self.assertEqual(issue.board_position, 2)

    def test_comment_mentions_are_synced_from_comment_body(self):
        issue = self.create_issue()
        comment = IssueComment.objects.create(
            issue=issue,
            author_user=self.assigned_user,
            body="Please coordinate with @analyst and @observer.",
        )

        mentions = list(comment.mentions.order_by("mentioned_as"))

        self.assertEqual([mention.mentioned_as for mention in mentions], ["analyst", "observer"])
        self.assertEqual(
            IssueCommentMention.objects.filter(issue_comment=comment).count(),
            2,
        )

        comment.body = "Only @observer needs follow-up."
        comment.save()

        mentions = list(comment.mentions.order_by("mentioned_as"))

        self.assertEqual([mention.mentioned_as for mention in mentions], ["observer"])

    def test_sync_mentions_can_be_called_explicitly(self):
        issue = self.create_issue()
        comment = IssueComment.objects.create(
            issue=issue,
            author_user=self.assigned_user,
            body="Check with @observer.",
        )

        queryset = IssueCommentController.sync_mentions(comment)

        self.assertEqual(queryset.count(), 1)

    def test_comment_mentions_are_synced_from_user_tokens(self):
        issue = self.create_issue()
        comment = IssueComment.objects.create(
            issue=issue,
            author_user=self.assigned_user,
            body="Loop in {{user:observer}} before closure.",
        )

        mentions = list(comment.mentions.order_by("mentioned_as"))

        self.assertEqual([mention.mentioned_as for mention in mentions], ["observer"])

    def test_sync_mentions_removes_all_mentions_when_body_has_none(self):
        issue = self.create_issue()
        comment = IssueComment.objects.create(
            issue=issue,
            author_user=self.assigned_user,
            body="Check with @observer.",
        )

        comment.body = "No mentions remain here."
        queryset = IssueCommentController.sync_mentions(comment)

        self.assertEqual(queryset.count(), 0)
        self.assertEqual(IssueCommentMention.objects.filter(issue_comment=comment).count(), 0)

    def test_string_representations_and_attachment_path_helper(self):
        issue = self.create_issue(group=self.group, user=self.assigned_user)
        comment = IssueComment.objects.create(
            issue=issue,
            author_user=self.assigned_user,
            body="Internal note",
        )
        mention = IssueCommentMention.objects.create(
            issue_comment=comment,
            mentioned_user=self.assigned_user,
            mentioned_as=self.assigned_user.username,
        )
        transition = IssueStateTransition.objects.create(
            issue=issue,
            from_state=WorkflowState.NEW,
            to_state=WorkflowState.TRIAGE,
            changed_by_user=self.assigned_user,
        )
        attachment = IssueAttachment(
            issue=issue,
            original_filename="network-log.txt",
            uploaded_by_user=self.assigned_user,
        )

        self.assertEqual(str(comment), f"{issue} comment by {self.assigned_user}")
        self.assertEqual(str(mention), f"@{self.assigned_user.username}")
        self.assertEqual(str(transition), f"{issue} NEW->TRIAGE")
        self.assertEqual(str(attachment), "network-log.txt")
        self.assertEqual(
            issue_attachment_upload_to(attachment, "network-log.txt"),
            f"issue-attachments/{issue.issue_number}/network-log.txt",
        )

        issue.issue_number = ""
        self.assertEqual(
            issue_attachment_upload_to(attachment, "network-log.txt"),
            f"issue-attachments/issue-{issue.pk}/network-log.txt",
        )
