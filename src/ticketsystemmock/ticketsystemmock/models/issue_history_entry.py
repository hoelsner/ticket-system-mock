from __future__ import annotations

from dataclasses import dataclass

from .base import ApiModel
from .user_summary import UserSummary


@dataclass(slots=True)
class IssueHistoryEntry(ApiModel):
    entry_type: str
    field_name: str
    message: str
    detail: str
    from_value: str
    to_value: str
    changed_at: str
    changed_by_user: UserSummary