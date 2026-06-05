from djangoapp.core.models import IssueAttachment

from .issue_controller import IssueController


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
        return attachment

    @staticmethod
    def update(issue_attachment, cleaned_data):
        attachment_file = cleaned_data.get("file")
        issue_attachment.description = cleaned_data.get("description", "").strip()
        if attachment_file:
            issue_attachment.file = attachment_file
            issue_attachment.original_filename = attachment_file.name
            issue_attachment.content_type = getattr(attachment_file, "content_type", "") or ""
            issue_attachment.file_size = getattr(attachment_file, "size", 0)
        issue_attachment.save()
        IssueController.touch(issue_attachment.issue)
        return issue_attachment
