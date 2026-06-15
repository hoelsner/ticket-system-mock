from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

from djangoapp.core.models import (
    Collection,
    DraftIssueAttachment,
    Issue,
    IssueAttachment,
    IssueCategory,
    IssueComment,
    IssueCommentMention,
    IssueDescriptionTemplate,
    IssueHistoryEvent,
    IssueStateTransition,
    WebhookDeliveryAttempt,
    WebhookEndpoint,
    WebhookEvent,
    WorkflowStateAutoAssignmentRule,
)


def _delete_stored_files(model, field_name, names):
    storage = model._meta.get_field(field_name).storage
    for name in names:
        if name:
            storage.delete(name)


class InstanceResetController:
    @staticmethod
    @transaction.atomic
    def reset(preserved_user):
        user_model = get_user_model()
        deleted_counts = {
            "workflow_state_auto_assignment_rules": WorkflowStateAutoAssignmentRule.objects.count(),
            "webhook_delivery_attempts": WebhookDeliveryAttempt.objects.count(),
            "webhook_events": WebhookEvent.objects.count(),
            "webhook_endpoints": WebhookEndpoint.objects.count(),
            "issue_comment_mentions": IssueCommentMention.objects.count(),
            "issue_comments": IssueComment.objects.count(),
            "issue_attachments": IssueAttachment.objects.count(),
            "issue_history_events": IssueHistoryEvent.objects.count(),
            "issue_state_transitions": IssueStateTransition.objects.count(),
            "issues": Issue.objects.count(),
            "issue_description_templates": IssueDescriptionTemplate.objects.count(),
            "draft_issue_attachments": DraftIssueAttachment.objects.count(),
            "groups": Group.objects.count(),
            "issue_categories": IssueCategory.objects.count(),
            "collections": Collection.objects.count(),
            "users": user_model.objects.exclude(pk=preserved_user.pk).count(),
        }
        attachment_file_names = list(IssueAttachment.objects.values_list("file", flat=True))
        draft_attachment_file_names = list(DraftIssueAttachment.objects.values_list("file", flat=True))
        deleted_user_avatar_names = list(
            user_model.objects.exclude(pk=preserved_user.pk).values_list("profile__avatar_image", flat=True)
        )

        WorkflowStateAutoAssignmentRule.objects.all().delete()
        WebhookDeliveryAttempt.objects.all().delete()
        WebhookEvent.objects.all().delete()
        WebhookEndpoint.objects.all().delete()
        Issue.objects.all().delete()
        IssueDescriptionTemplate.objects.all().delete()
        DraftIssueAttachment.objects.all().delete()
        Group.objects.all().delete()
        IssueCategory.objects.all().delete()
        Collection.objects.all().delete()
        user_model.objects.exclude(pk=preserved_user.pk).delete()

        _delete_stored_files(IssueAttachment, "file", attachment_file_names)
        _delete_stored_files(DraftIssueAttachment, "file", draft_attachment_file_names)
        _delete_stored_files(
            user_model._meta.get_field("profile").related_model, "avatar_image", deleted_user_avatar_names
        )

        return deleted_counts
