import uuid

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from djangoapp.core.models import (
    WebhookDeliveryStatus,
    WebhookEndpoint,
    WebhookEvent,
    WebhookEventType,
    WorkflowState,
)

from .webhook_delivery_controller import WebhookDeliveryController


class WebhookController:
    CHANGE_FIELD_NAMES = (
        "title",
        "description",
        "priority",
        "workflow_state",
        "collection",
        "category",
        "queue",
        "assigned_user",
        "is_escalated",
        "resolved_at",
        "closed_at",
    )

    @staticmethod
    def capture_issue_snapshot(issue):
        return {
            "title": issue.title,
            "description": issue.description_markdown,
            "priority": issue.priority,
            "workflow_state": issue.workflow_state,
            "collection": WebhookController._serialize_collection(issue.collection),
            "category": WebhookController._serialize_category(issue.category),
            "queue": WebhookController._serialize_group(issue.group),
            "assigned_user": WebhookController._serialize_user(issue.user),
            "is_escalated": issue.is_escalated,
            "resolved_at": WebhookController._serialize_datetime(issue.resolved_at),
            "closed_at": WebhookController._serialize_datetime(issue.closed_at),
        }

    @staticmethod
    def create_issue_created_event(issue, actor=None):
        return WebhookController._create_event(
            issue,
            WebhookEventType.ISSUE_CREATED,
            actor=actor,
        )

    @staticmethod
    def create_issue_updated_event(issue, previous_snapshot, actor=None):
        current_snapshot = WebhookController.capture_issue_snapshot(issue)
        changes = WebhookController._build_changes(previous_snapshot, current_snapshot)
        if not changes:
            return None

        return WebhookController._create_event(
            issue,
            WebhookEventType.ISSUE_UPDATED,
            actor=actor,
            changes=changes,
        )

    @staticmethod
    def create_issue_queue_assigned_event(issue, previous_snapshot, actor=None):
        current_snapshot = WebhookController.capture_issue_snapshot(issue)
        if previous_snapshot["queue"] == current_snapshot["queue"]:
            return None

        return WebhookController._create_event(
            issue,
            WebhookEventType.ISSUE_QUEUE_ASSIGNED,
            actor=actor,
            transition={
                "from_queue": previous_snapshot["queue"],
                "to_queue": current_snapshot["queue"],
                "from_state": previous_snapshot["workflow_state"],
                "to_state": current_snapshot["workflow_state"],
            },
        )

    @staticmethod
    def create_issue_commented_event(comment, actor=None):
        return WebhookController._create_event(
            comment.issue,
            WebhookEventType.ISSUE_COMMENTED,
            actor=actor or comment.author_user,
            comment=WebhookController._serialize_comment(comment),
        )

    @staticmethod
    def create_issue_closed_event(issue, actor=None, transition=None):
        if issue.workflow_state != WorkflowState.CLOSED:
            return None

        payload = {}
        if transition is not None:
            payload["transition"] = {
                "from_state": transition.from_state,
                "to_state": transition.to_state,
                "from_queue": None,
                "to_queue": WebhookController._serialize_group(issue.group),
            }

        return WebhookController._create_event(
            issue,
            WebhookEventType.ISSUE_CLOSED,
            actor=actor,
            **payload,
        )

    @staticmethod
    def _create_event(issue, event_type, actor=None, **extra_payload):
        event_id = uuid.uuid4()
        occurred_at = WebhookController._get_occurred_at(issue, event_type)
        target_endpoint_ids = WebhookController._get_target_endpoint_ids(event_type)
        payload = WebhookController._build_event_payload(
            issue,
            event_id,
            event_type,
            occurred_at,
            actor,
        )
        payload.update({key: value for key, value in extra_payload.items() if value is not None})

        webhook_event = WebhookEvent.objects.create(
            id=event_id,
            event_type=event_type,
            issue=issue,
            occurred_at=occurred_at,
            target_endpoint_ids=target_endpoint_ids,
            payload=payload,
            delivery_status=WebhookController._get_initial_delivery_status(target_endpoint_ids),
        )

        if target_endpoint_ids:
            transaction.on_commit(lambda: WebhookDeliveryController.dispatch_event_async(webhook_event.pk))

        return webhook_event

    @staticmethod
    def _get_occurred_at(issue, event_type):
        if event_type == WebhookEventType.ISSUE_CLOSED:
            return issue.closed_at
        return timezone.now()

    @staticmethod
    def _build_event_payload(issue, event_id, event_type, occurred_at, actor):
        return {
            "base_url": settings.SERVICE_BASE_URL.rstrip("/"),
            "event_id": str(event_id),
            "event_type": event_type,
            "occurred_at": WebhookController._serialize_datetime_value(occurred_at),
            "actor": WebhookController._serialize_actor(actor),
            "issue": WebhookController._serialize_issue(issue),
        }

    @staticmethod
    def _get_initial_delivery_status(target_endpoint_ids):
        if target_endpoint_ids:
            return WebhookDeliveryStatus.PENDING
        return WebhookDeliveryStatus.SUCCESS

    @staticmethod
    def _get_target_endpoint_ids(event_type):
        return [
            endpoint.pk
            for endpoint in WebhookEndpoint.objects.filter(enabled=True).order_by("pk")
            if endpoint.is_subscribed_to(event_type)
        ]

    @staticmethod
    def _build_changes(previous_snapshot, current_snapshot):
        changes = {}
        for field_name in WebhookController.CHANGE_FIELD_NAMES:
            if previous_snapshot[field_name] == current_snapshot[field_name]:
                continue
            changes[field_name] = {
                "from": previous_snapshot[field_name],
                "to": current_snapshot[field_name],
            }
        return changes

    @staticmethod
    def _serialize_issue(issue):
        return {
            "id": issue.pk,
            "key": issue.issue_number,
            "title": issue.title,
            "description": issue.description_markdown,
            "workflow_state": issue.workflow_state,
            "priority": issue.priority,
            "collection": WebhookController._serialize_collection(issue.collection),
            "category": WebhookController._serialize_category(issue.category),
            "queue": WebhookController._serialize_group(issue.group),
            "assigned_user": WebhookController._serialize_user(issue.user),
            "is_escalated": issue.is_escalated,
            "created_at": WebhookController._serialize_datetime(issue.created_at),
            "updated_at": WebhookController._serialize_datetime(issue.updated_at),
            "resolved_at": WebhookController._serialize_datetime(issue.resolved_at),
            "closed_at": WebhookController._serialize_datetime(issue.closed_at),
            "links": WebhookController._serialize_issue_links(issue),
        }

    @staticmethod
    def _serialize_comment(comment):
        return {
            "id": comment.pk,
            "type": comment.visibility.lower(),
            "body": comment.body,
            "visibility": comment.visibility,
            "created_at": WebhookController._serialize_datetime(comment.created_at),
            "author": WebhookController._serialize_actor(comment.author_user),
        }

    @staticmethod
    def _serialize_actor(user):
        if user is None:
            return None
        return {
            "id": user.pk,
            "type": "user",
            "display_name": WebhookController._get_user_display_name(user),
        }

    @staticmethod
    def _serialize_user(user):
        if user is None:
            return None
        return {
            "id": user.pk,
            "username": user.get_username(),
            "display_name": WebhookController._get_user_display_name(user),
        }

    @staticmethod
    def _serialize_group(group):
        if group is None:
            return None
        return {
            "id": group.pk,
            "name": group.name,
        }

    @staticmethod
    def _serialize_collection(collection):
        return {
            "id": collection.pk,
            "name": collection.name,
            "prefix": collection.prefix,
        }

    @staticmethod
    def _serialize_category(category):
        return {
            "id": category.pk,
            "name": category.name,
            "code": category.code,
        }

    @staticmethod
    def _serialize_datetime(value):
        if value is None:
            return None
        return WebhookController._serialize_datetime_value(value)

    @staticmethod
    def _serialize_datetime_value(value):
        if value is None:
            return None
        return value.isoformat().replace("+00:00", "Z")

    @staticmethod
    def _serialize_issue_links(issue):
        base_url = settings.SERVICE_BASE_URL.rstrip("/")
        return {
            "detail": f"{base_url}{reverse('issue-detail', kwargs={'pk': issue.pk})}",
            "api": f"{base_url}/api/issues/{issue.pk}",
        }

    @staticmethod
    def _get_user_display_name(user):
        return user.get_full_name() or user.get_username()
