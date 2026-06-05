from django.conf import settings
from django.db import models


class IssueCommentMention(models.Model):
    issue_comment = models.ForeignKey(
        "core.IssueComment",
        on_delete=models.CASCADE,
        related_name="mentions",
    )
    mentioned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="issue_comment_mentions",
    )
    mentioned_as = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["issue_comment", "mentioned_user", "mentioned_as"],
                name="core_issue_comment_mention_unique_reference",
            )
        ]

    def __str__(self):
        return f"@{self.mentioned_as}"