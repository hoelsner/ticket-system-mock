from __future__ import annotations

from dataclasses import dataclass

from .base import ApiModel
from .issue_comment import MentionedComment
from .issue_summary import IssueSummary


@dataclass(slots=True)
class DashboardResponse(ApiModel):
    assigned_issues: list[IssueSummary]
    mentioned_comments: list[MentionedComment]
