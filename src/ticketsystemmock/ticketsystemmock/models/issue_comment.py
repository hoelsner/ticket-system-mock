from __future__ import annotations

from dataclasses import dataclass

from .base import ApiModel
from .issue_summary import IssueSummary
from .user_summary import UserSummary


@dataclass(slots=True)
class IssueComment(ApiModel):
    id: int
    body: str
    visibility: str
    visibility_label: str
    created_at: str
    author_user: UserSummary


@dataclass(slots=True)
class MentionedComment(ApiModel):
    id: int
    issue: "IssueSummary"
    body: str
    visibility: str
    visibility_label: str
    created_at: str
    author_user: UserSummary


@dataclass(slots=True)
class IssueCommentMutation(ApiModel):
    status: str
    comment: IssueComment
