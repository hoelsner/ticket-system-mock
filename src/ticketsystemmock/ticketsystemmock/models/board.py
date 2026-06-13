from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import ApiModel
from .collection import Collection
from .issue_category import IssueCategory
from .issue_summary import IssueSummary
from .user_summary import UserSummary


@dataclass(slots=True)
class BoardColumn(ApiModel):
    value: str
    label: str
    is_open: bool
    issue_count: int
    issues: list[IssueSummary]


@dataclass(slots=True)
class BoardResponse(ApiModel):
    search_query: str
    selected_assignee: str
    selected_priority: str
    selected_collection: str
    selected_category: str
    selected_group: str | None = None
    selected_is_escalated: str | None = None
    selected_updated_within_seconds: str | None = None
    assignee_options: list[UserSummary] = field(default_factory=list)
    priority_options: list[dict[str, Any]] = field(default_factory=list)
    collection_options: list[Collection] = field(default_factory=list)
    category_options: list[IssueCategory] = field(default_factory=list)
    board_columns: list[BoardColumn] = field(default_factory=list)
    board_issue_count: int = 0