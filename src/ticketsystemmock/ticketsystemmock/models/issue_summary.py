from __future__ import annotations

from dataclasses import dataclass

from .base import ApiModel
from .collection import Collection
from .group import Group
from .issue_category import IssueCategory
from .user_summary import UserSummary


@dataclass(slots=True)
class IssueSummary(ApiModel):
    id: int
    issue_number: str
    title: str
    description_markdown: str
    priority: str
    priority_label: str
    workflow_state: str
    workflow_state_label: str
    board_position: int
    is_escalated: bool
    created_at: str
    updated_at: str
    resolved_at: str | None
    closed_at: str | None
    archived_at: str | None
    collection: Collection
    category: IssueCategory | None
    group: Group | None
    user: UserSummary | None
