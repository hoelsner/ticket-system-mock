import json
from queue import Empty
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from djangoapp.core.models import Collection, Issue, IssueCategory, IssuePriority, WorkflowState
from djangoapp.user_interface.board_events import BoardEventBroker, board_event_broker
from djangoapp.user_interface.views import BoardEventStreamView


class BoardEventBrokerTests(SimpleTestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def test_board_event_broker_publishes_to_subscribers(self):
        broker = BoardEventBroker()
        subscriber_id, subscriber = broker.subscribe()

        broker.publish("kanban.board.updated", {"scope": "board"})
        event_name, event_data = broker.next_event(subscriber)
        broker.unsubscribe(subscriber_id)

        self.assertEqual(event_name, "kanban.board.updated")
        self.assertEqual(json.loads(event_data), {"scope": "board"})

    def test_board_event_broker_returns_keepalive_when_idle(self):
        broker = BoardEventBroker()
        _subscriber_id, subscriber = broker.subscribe()

        with mock.patch.object(subscriber, "get", side_effect=Empty):
            event_name, event_data = broker.next_event(subscriber)

        self.assertEqual(event_name, "keepalive")
        self.assertEqual(json.loads(event_data), {})

    def test_board_event_stream_emits_board_update(self):
        request = self.request_factory.get(reverse("board-events"))
        request.user = mock.Mock(is_authenticated=True)

        response = BoardEventStreamView.as_view()(request)
        board_event_broker.publish("kanban.board.updated", {"scope": "board"})
        first_chunk = next(response.streaming_content)
        response.close()

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"event: kanban.board.updated", first_chunk)


class BoardSyncTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="demo-sync",
            password="demo-password-123",
        )
        self.collection = Collection.objects.get(prefix="TASK")
        self.category = IssueCategory.objects.create(name="Operations", code="OPS")

    def create_issue(self, **overrides):
        payload = {
            "title": "New issue",
            "description_markdown": "Board sync fixture.",
            "collection": self.collection,
            "category": self.category,
            "workflow_state": WorkflowState.NEW,
            "priority": IssuePriority.HIGH,
        }
        payload.update(overrides)
        return Issue.objects.create(**payload)

    def test_board_fragment_view_renders_flat_board_markup(self):
        self.create_issue(title="Visible new issue")
        self.client.force_login(self.user)

        response = self.client.get(reverse("board-fragment"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-kanban-board-shell")
        self.assertContains(response, "data-kanban-card-wrapper")
        self.assertNotContains(response, "kanban-priority-pane")

    def test_board_fragment_without_matching_issues_still_renders_empty_columns(self):
        self.create_issue(title="Visible new issue")
        self.client.force_login(self.user)

        response = self.client.get(reverse("board-fragment"), {"search": "printer"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-kanban-board-shell")
        self.assertContains(response, "data-kanban-column")
        self.assertContains(response, "kanban-column__empty")
        self.assertNotContains(response, "No matching issues")
        self.assertNotContains(response, "Visible new issue")

    def test_issue_move_view_rejects_invalid_state(self):
        issue = self.create_issue()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-move", args=[issue.pk]),
            data=json.dumps({"target_state": "INVALID", "position_index": 0}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_issue_move_view_rejects_invalid_position(self):
        issue = self.create_issue()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-move", args=[issue.pk]),
            data=json.dumps({"target_state": WorkflowState.NEW, "position_index": "invalid"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_issue_move_view_rejects_invalid_json_payload(self):
        issue = self.create_issue()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-move", args=[issue.pk]),
            data="{",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
