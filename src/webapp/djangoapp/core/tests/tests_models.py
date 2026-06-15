from unittest.mock import patch

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
    IssueDescriptionTemplate,
    IssuePriority,
    IssueStateTransition,
    WebhookEndpoint,
    WebhookEvent,
    WebhookEventType,
    WorkflowState,
    WorkflowStateAutoAssignmentRule,
    issue_attachment_upload_to,
)
from djangoapp.user_interface import controllers as user_interface_controllers


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
        self.assertEqual(issue.workflow_state, WorkflowState.NEW)
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

    def test_issue_allows_missing_category(self):
        issue = Issue.objects.create(
            title="Unclassified outage",
            description_markdown="Category pending during intake.",
            collection=self.collection,
        )

        self.assertIsNone(issue.category)

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

    def test_issue_description_template_requires_collection_or_category(self):
        template = IssueDescriptionTemplate(
            name="Generic outage",
            description_markdown="## Summary",
        )

        with self.assertRaises(ValidationError) as error:
            template.full_clean()

        self.assertIn("collection", error.exception.message_dict)
        self.assertIn("category", error.exception.message_dict)

    def test_issue_description_template_allows_collection_and_category_scope(self):
        template = IssueDescriptionTemplate.objects.create(
            name="Database incident",
            description_markdown="## Impact",
            collection=self.collection,
            category=self.category,
        )

        self.assertEqual(template.collection, self.collection)
        self.assertEqual(template.category, self.category)

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
        self.assertEqual(transition.from_state, WorkflowState.NEW)
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

    def test_workflow_state_auto_assignment_rule_requires_user_to_belong_to_group(self):
        rule = WorkflowStateAutoAssignmentRule(
            workflow_state=WorkflowState.ASSIGNED,
            group=self.group,
            user=self.other_user,
        )

        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_update_workflow_state_applies_matching_auto_assignment_rule(self):
        issue = self.create_issue()
        WorkflowStateAutoAssignmentRule.objects.create(
            workflow_state=WorkflowState.ASSIGNED,
            group=self.group,
            user=self.assigned_user,
        )

        updated_issue, transition = IssueController.update_workflow_state(
            issue,
            WorkflowState.ASSIGNED,
            changed_by_user=self.assigned_user,
        )

        updated_issue.refresh_from_db()

        self.assertEqual(updated_issue.workflow_state, WorkflowState.ASSIGNED)
        self.assertEqual(updated_issue.group, self.group)
        self.assertEqual(updated_issue.user, self.assigned_user)
        self.assertIsNotNone(transition)

    def test_update_workflow_state_assigns_group_and_clears_user_when_rule_has_no_user(self):
        issue = self.create_issue(group=self.group, user=self.assigned_user)
        other_group = Group.objects.create(name="Field Operations")
        WorkflowStateAutoAssignmentRule.objects.create(
            workflow_state=WorkflowState.WAITING,
            group=other_group,
        )

        updated_issue, _transition = IssueController.update_workflow_state(
            issue,
            WorkflowState.WAITING,
            changed_by_user=self.assigned_user,
        )

        updated_issue.refresh_from_db()

        self.assertEqual(updated_issue.group, other_group)
        self.assertIsNone(updated_issue.user)

    def test_update_workflow_state_keeps_assignments_when_no_auto_assignment_rule_matches(self):
        issue = self.create_issue(group=self.group, user=self.assigned_user)

        updated_issue, _transition = IssueController.update_workflow_state(
            issue,
            WorkflowState.IN_PROGRESS,
            changed_by_user=self.assigned_user,
        )

        updated_issue.refresh_from_db()

        self.assertEqual(updated_issue.group, self.group)
        self.assertEqual(updated_issue.user, self.assigned_user)

    @patch("djangoapp.core.controllers.webhook_delivery_controller.WebhookDeliveryController.dispatch_event_async")
    def test_create_issue_emits_webhook_created_event(self, _dispatch_event_async):
        endpoint = WebhookEndpoint.objects.create(
            name="Lifecycle sink",
            target_url="https://example.com/webhooks/issues",
            subscribed_event_types=[WebhookEventType.ISSUE_CREATED],
        )

        issue = user_interface_controllers.create_issue(
            {
                "title": "Webhook issue",
                "description_markdown": "Created through controller.",
                "collection": self.collection,
                "category": self.category,
                "priority": IssuePriority.MEDIUM,
                "group": None,
                "user": None,
                "is_escalated": False,
            },
            self.assigned_user,
        )

        webhook_event = WebhookEvent.objects.get(event_type=WebhookEventType.ISSUE_CREATED)

        self.assertEqual(webhook_event.issue, issue)
        self.assertEqual(webhook_event.target_endpoint_ids, [endpoint.pk])
        self.assertEqual(webhook_event.payload["event"], WebhookEventType.ISSUE_CREATED)
        self.assertEqual(webhook_event.payload["data"]["key"], issue.issue_number)
        self.assertEqual(webhook_event.payload["actor"]["id"], self.assigned_user.pk)

    @patch("djangoapp.core.controllers.webhook_delivery_controller.WebhookDeliveryController.dispatch_event_async")
    def test_update_issue_emits_update_and_queue_assignment_events(self, _dispatch_event_async):
        WebhookEndpoint.objects.create(
            name="Update sink",
            target_url="https://example.com/webhooks/updates",
            subscribed_event_types=[
                WebhookEventType.ISSUE_UPDATED,
                WebhookEventType.ISSUE_QUEUE_ASSIGNED,
            ],
        )
        issue = self.create_issue()

        user_interface_controllers.update_issue(
            issue,
            {
                "title": "Updated switch outage",
                "description_markdown": "Updated description.",
                "collection": self.collection,
                "category": self.category,
                "priority": IssuePriority.HIGH,
                "workflow_state": WorkflowState.ASSIGNED,
                "group": self.group,
                "user": self.assigned_user,
                "is_escalated": True,
                "transition_reason": "Assigned to the network group",
            },
            self.assigned_user,
        )

        update_event = WebhookEvent.objects.get(event_type=WebhookEventType.ISSUE_UPDATED)
        queue_event = WebhookEvent.objects.get(event_type=WebhookEventType.ISSUE_QUEUE_ASSIGNED)

        self.assertIn("workflow_state", update_event.payload["changes"])
        self.assertIn("queue", update_event.payload["changes"])
        self.assertEqual(queue_event.payload["transition"]["to_queue"]["id"], self.group.pk)
        self.assertIsNone(queue_event.payload["transition"]["from_queue"])

    @patch("djangoapp.core.controllers.webhook_delivery_controller.WebhookDeliveryController.dispatch_event_async")
    def test_issue_comment_signal_emits_comment_event(self, _dispatch_event_async):
        WebhookEndpoint.objects.create(
            name="Comment sink",
            target_url="https://example.com/webhooks/comments",
            subscribed_event_types=[WebhookEventType.ISSUE_COMMENTED],
        )
        issue = self.create_issue()

        comment = user_interface_controllers.add_issue_comment(
            issue,
            {
                "body": "Need network logs.",
                "visibility": "INTERNAL",
            },
            self.assigned_user,
        )

        webhook_event = WebhookEvent.objects.get(event_type=WebhookEventType.ISSUE_COMMENTED)

        self.assertEqual(webhook_event.issue, issue)
        self.assertEqual(webhook_event.payload["event"], WebhookEventType.ISSUE_COMMENTED)
        self.assertEqual(webhook_event.payload["comment"]["id"], comment.pk)
        self.assertEqual(webhook_event.payload["comment"]["visibility"], "INTERNAL")

    @patch("djangoapp.core.controllers.webhook_delivery_controller.WebhookDeliveryController.dispatch_event_async")
    def test_closing_issue_emits_closed_event(self, _dispatch_event_async):
        WebhookEndpoint.objects.create(
            name="Closed sink",
            target_url="https://example.com/webhooks/closed",
            subscribed_event_types=[WebhookEventType.ISSUE_CLOSED],
        )
        issue = self.create_issue(group=self.group, user=self.assigned_user)

        IssueController.update_workflow_state(
            issue,
            WorkflowState.CLOSED,
            changed_by_user=self.assigned_user,
        )

        webhook_event = WebhookEvent.objects.get(event_type=WebhookEventType.ISSUE_CLOSED)

        self.assertEqual(webhook_event.payload["event"], WebhookEventType.ISSUE_CLOSED)
        self.assertEqual(webhook_event.payload["data"]["workflow_state"], WorkflowState.CLOSED)
        self.assertEqual(webhook_event.payload["actor"]["id"], self.assigned_user.pk)

    def test_update_workflow_state_is_noop_when_state_does_not_change(self):
        issue = self.create_issue()

        updated_issue, transition = IssueController.update_workflow_state(
            issue,
            WorkflowState.NEW,
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
            WorkflowState.NEW,
            changed_by_user=self.assigned_user,
            position_index=0,
            reason="Prioritize within new issues",
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
        IssueController.sync_board_position(issue, WorkflowState.NEW, IssuePriority.MEDIUM)

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
