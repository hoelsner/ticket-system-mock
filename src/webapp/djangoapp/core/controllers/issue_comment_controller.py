import re

from django.contrib.auth import get_user_model
from django.db import transaction

from djangoapp.core.models import IssueCommentMention

from .issue_controller import IssueController

User = get_user_model()

MENTION_PATTERN = re.compile(r"(?<!\w)@(?P<username>[\w.@+-]+)")
TOKEN_MENTION_PATTERN = re.compile(r"\{\{\s*user\s*:\s*(?P<username>[\w.@+-]+)\s*\}\}")


def _extract_usernames(text):
    direct_usernames = {
        match.group("username").rstrip(".,:;!?")
        for match in MENTION_PATTERN.finditer(text)
        if match.group("username").rstrip(".,:;!?")
    }
    token_usernames = {
        match.group("username").strip().rstrip(".,:;!?")
        for match in TOKEN_MENTION_PATTERN.finditer(text)
        if match.group("username").strip().rstrip(".,:;!?")
    }
    return direct_usernames | token_usernames


class IssueCommentController:
    @staticmethod
    def update(issue_comment, cleaned_data):
        issue_comment.body = cleaned_data["body"]
        issue_comment.visibility = cleaned_data["visibility"]
        issue_comment.save()
        IssueController.touch(issue_comment.issue)
        return issue_comment

    @staticmethod
    @transaction.atomic
    def sync_mentions(issue_comment):
        usernames = _extract_usernames(issue_comment.body)

        IssueCommentMention.objects.filter(issue_comment=issue_comment).exclude(mentioned_as__in=usernames).delete()

        users = list(User.objects.filter(username__in=usernames))

        mentions_to_create = [
            IssueCommentMention(
                issue_comment=issue_comment,
                mentioned_user=user,
                mentioned_as=user.username,
            )
            for user in users
        ]

        if mentions_to_create:
            IssueCommentMention.objects.bulk_create(mentions_to_create, ignore_conflicts=True)

        return issue_comment.mentions.select_related("mentioned_user")
