from django.conf import settings
from django.db import models

from .issue_comment_visibility import IssueCommentVisibility


class IssueComment(models.Model):
    issue = models.ForeignKey(
        "core.Issue",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="issue_comments",
    )
    body = models.TextField()
    visibility = models.CharField(
        max_length=24,
        choices=IssueCommentVisibility.choices,
        default=IssueCommentVisibility.INTERNAL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.issue} comment by {self.author_user}"
