def issue_attachment_upload_to(instance, filename):
    issue_number = instance.issue.issue_number or f"issue-{instance.issue_id}"
    return f"issue-attachments/{issue_number}/{filename}"


def draft_issue_attachment_upload_to(instance, filename):
    return f"issue-attachment-drafts/{instance.draft_token}/{filename}"
