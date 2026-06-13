from __future__ import annotations

from dataclasses import dataclass

from .base import ApiModel
from .user_summary import UserSummary


@dataclass(slots=True)
class IssueTransition(ApiModel):
    id: int
    from_state: str
    from_state_label: str
    to_state: str
    to_state_label: str
    changed_at: str
    reason: str
    changed_by_user: UserSummary