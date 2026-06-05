from django.db.models.signals import post_save
from django.dispatch import receiver

from .controllers import IssueCommentController
from .models import IssueComment


@receiver(post_save, sender=IssueComment)
def sync_issue_comment_mentions(sender, instance, **kwargs):
    IssueCommentController.sync_mentions(instance)
