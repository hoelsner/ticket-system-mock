from django.conf import settings
from django.db import models

from .attachment_paths import issue_attachment_upload_to


class IssueAttachment(models.Model):
    issue = models.ForeignKey(
        "core.Issue",
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to=issue_attachment_upload_to)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveBigIntegerField(default=0)
    description = models.CharField(max_length=255, blank=True)
    uploaded_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_issue_attachments",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.original_filename