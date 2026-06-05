from django.conf import settings
from django.db import models

from .attachment_paths import draft_issue_attachment_upload_to


class DraftIssueAttachment(models.Model):
    draft_token = models.CharField(max_length=64, db_index=True)
    file = models.FileField(upload_to=draft_issue_attachment_upload_to)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveBigIntegerField(default=0)
    description = models.CharField(max_length=255, blank=True)
    uploaded_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_draft_issue_attachments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return self.original_filename
