from django.db import transaction

from djangoapp.core.models import IssueHistoryEvent

from .webhook_controller import WebhookController


class IssueHistoryController:
    SNAPSHOT_FIELD_MAP = {
        "title": "title",
        "description": "description",
        "priority": "priority",
        "collection": "collection",
        "category": "category",
        "queue": "group",
        "assigned_user": "user",
        "is_escalated": "is_escalated",
        "resolved_at": "resolved_at",
        "closed_at": "closed_at",
        "archived_at": "archived_at",
        "archived_by_user": "archived_by_user",
    }

    @staticmethod
    @transaction.atomic
    def record_snapshot_changes(issue, previous_snapshot, changed_by_user):
        current_snapshot = WebhookController.capture_issue_snapshot(issue)
        changes = WebhookController._build_changes(previous_snapshot, current_snapshot)
        history_events = [
            IssueHistoryController._build_snapshot_change_event(
                issue,
                snapshot_field_name,
                changes[snapshot_field_name],
                changed_by_user,
            )
            for snapshot_field_name in IssueHistoryController._tracked_snapshot_field_names(changes)
        ]

        if not history_events:
            return []

        return IssueHistoryEvent.objects.bulk_create(history_events)

    @staticmethod
    def record_attachment_added(issue, attachment, changed_by_user):
        return IssueHistoryEvent.objects.create(
            issue=issue,
            event_type=IssueHistoryEvent.ATTACHMENT_ADDED,
            field_name="attachment",
            old_value="",
            new_value=IssueHistoryController._serialize_attachment_value_from_attachment(attachment),
            changed_by_user=changed_by_user,
        )

    @staticmethod
    def record_attachment_updated(issue, previous_attachment_snapshot, attachment, changed_by_user):
        old_value = IssueHistoryController._serialize_attachment_value_from_snapshot(previous_attachment_snapshot)
        new_value = IssueHistoryController._serialize_attachment_value_from_attachment(attachment)
        if old_value == new_value:
            return None

        return IssueHistoryEvent.objects.create(
            issue=issue,
            event_type=IssueHistoryEvent.ATTACHMENT_UPDATED,
            field_name="attachment",
            old_value=old_value,
            new_value=new_value,
            changed_by_user=changed_by_user,
        )

    @staticmethod
    def record_attachment_removed(issue, previous_attachment_snapshot, changed_by_user):
        return IssueHistoryEvent.objects.create(
            issue=issue,
            event_type=IssueHistoryEvent.ATTACHMENT_REMOVED,
            field_name="attachment",
            old_value=IssueHistoryController._serialize_attachment_value_from_snapshot(previous_attachment_snapshot),
            new_value="",
            changed_by_user=changed_by_user,
        )

    @staticmethod
    def capture_attachment_snapshot(issue_attachment):
        return {
            "original_filename": issue_attachment.original_filename,
            "description": issue_attachment.description,
        }

    @staticmethod
    def _build_snapshot_change_event(issue, snapshot_field_name, field_change, changed_by_user):
        return IssueHistoryEvent(
            issue=issue,
            event_type=IssueHistoryEvent.FIELD_CHANGED,
            field_name=IssueHistoryController.SNAPSHOT_FIELD_MAP[snapshot_field_name],
            old_value=IssueHistoryController._serialize_snapshot_value(
                snapshot_field_name,
                field_change["from"],
            ),
            new_value=IssueHistoryController._serialize_snapshot_value(
                snapshot_field_name,
                field_change["to"],
            ),
            changed_by_user=changed_by_user,
        )

    @staticmethod
    def _tracked_snapshot_field_names(changes):
        return [
            snapshot_field_name
            for snapshot_field_name in IssueHistoryController.SNAPSHOT_FIELD_MAP
            if snapshot_field_name in changes
        ]

    @staticmethod
    def _serialize_snapshot_value(field_name, value):
        serializer = getattr(
            IssueHistoryController,
            f"_serialize_{field_name}_snapshot_value",
            IssueHistoryController._serialize_default_snapshot_value,
        )
        return serializer(value)

    @staticmethod
    def _serialize_description_snapshot_value(value):
        return (value or "").strip()

    @staticmethod
    def _serialize_title_snapshot_value(value):
        return IssueHistoryController._serialize_description_snapshot_value(value)

    @staticmethod
    def _serialize_priority_snapshot_value(value):
        priority_labels = {
            "LOW": "Low",
            "MEDIUM": "Medium",
            "HIGH": "High",
            "CRITICAL": "Critical",
        }
        return priority_labels.get(value, IssueHistoryController._serialize_default_snapshot_value(value))

    @staticmethod
    def _serialize_collection_snapshot_value(value):
        return IssueHistoryController._relation_display(value, "name")

    @staticmethod
    def _serialize_category_snapshot_value(value):
        return IssueHistoryController._relation_display(value, "name")

    @staticmethod
    def _serialize_queue_snapshot_value(value):
        return IssueHistoryController._relation_display(value, "name")

    @staticmethod
    def _serialize_assigned_user_snapshot_value(value):
        return IssueHistoryController._relation_display(value, "display_name")

    @staticmethod
    def _serialize_archived_by_user_snapshot_value(value):
        return IssueHistoryController._relation_display(value, "display_name")

    @staticmethod
    def _serialize_is_escalated_snapshot_value(value):
        return "Enabled" if value else "Disabled"

    @staticmethod
    def _serialize_default_snapshot_value(value):
        if value is None:
            return ""
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    @staticmethod
    def _relation_display(value, key):
        return (value or {}).get(key) or "Unassigned"

    @staticmethod
    def _serialize_attachment_value_from_attachment(attachment):
        return IssueHistoryController._serialize_attachment_value_from_snapshot(
            IssueHistoryController.capture_attachment_snapshot(attachment)
        )

    @staticmethod
    def _serialize_attachment_value_from_snapshot(snapshot):
        return IssueHistoryController._format_attachment_value(
            snapshot.get("original_filename"),
            snapshot.get("description"),
        )

    @staticmethod
    def _format_attachment_value(filename, description):
        cleaned_description = IssueHistoryController._clean_attachment_description(description)
        cleaned_filename = IssueHistoryController._clean_attachment_filename(filename)
        return f"{cleaned_filename}{IssueHistoryController._attachment_value_suffix(cleaned_description)}"

    @staticmethod
    def _clean_attachment_description(description):
        return (description or "").strip()

    @staticmethod
    def _clean_attachment_filename(filename):
        return filename or "Unnamed attachment"

    @staticmethod
    def _attachment_value_suffix(description):
        if not description:
            return ""
        return f" ({description})"
