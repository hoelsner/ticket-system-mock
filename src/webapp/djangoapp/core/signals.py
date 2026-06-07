from django.db.models.signals import post_save
from django.dispatch import receiver

from .controllers import IssueCommentController, WebhookController
from .models import IssueComment


@receiver(post_save, sender=IssueComment)
def sync_issue_comment_mentions(sender, instance, created=False, **kwargs):
    IssueCommentController.sync_mentions(instance)
    if created:
        WebhookController.create_issue_commented_event(instance, actor=instance.author_user)
