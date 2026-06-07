from djangoapp.core.models import IssueAttachment

from .issue_controller import IssueController
from .issue_history_controller import IssueHistoryController


class IssueAttachmentController:
    @staticmethod
    def create(issue, cleaned_data, uploaded_by_user):
        attachment_file = cleaned_data["file"]
        attachment = IssueAttachment.objects.create(
            issue=issue,
            file=attachment_file,
            original_filename=attachment_file.name,
            content_type=getattr(attachment_file, "content_type", "") or "",
            file_size=getattr(attachment_file, "size", 0),
            description=cleaned_data.get("description", "").strip(),
            uploaded_by_user=uploaded_by_user,
        )
        IssueController.touch(issue)
        IssueHistoryController.record_attachment_added(issue, attachment, uploaded_by_user)
        return attachment

    @staticmethod
    def update(issue_attachment, cleaned_data, changed_by_user):
        previous_attachment_snapshot = IssueHistoryController.capture_attachment_snapshot(issue_attachment)
        attachment_file = cleaned_data.get("file")
        issue_attachment.description = cleaned_data.get("description", "").strip()
        if attachment_file:
            issue_attachment.file = attachment_file
            issue_attachment.original_filename = attachment_file.name
            issue_attachment.content_type = getattr(attachment_file, "content_type", "") or ""
            issue_attachment.file_size = getattr(attachment_file, "size", 0)
        issue_attachment.save()
        IssueController.touch(issue_attachment.issue)
        IssueHistoryController.record_attachment_updated(
            issue_attachment.issue,
            previous_attachment_snapshot,
            issue_attachment,
            changed_by_user,
        )
        return issue_attachment

    @staticmethod
    def delete(issue_attachment, deleted_by_user):
        previous_attachment_snapshot = IssueHistoryController.capture_attachment_snapshot(issue_attachment)
        issue = issue_attachment.issue
        issue_attachment.file.delete(save=False)
        issue_attachment.delete()
        IssueController.touch(issue)
        IssueHistoryController.record_attachment_removed(issue, previous_attachment_snapshot, deleted_by_user)
        return issue
