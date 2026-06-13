from __future__ import annotations

from dataclasses import dataclass

from .base import ApiModel
from .issue_attachment import IssueAttachment
from .issue_comment import IssueComment
from .issue_history_entry import IssueHistoryEntry
from .issue_summary import IssueSummary
from .issue_transition import IssueTransition


@dataclass(slots=True)
class IssueDetail(IssueSummary):
    attachments: list[IssueAttachment]
    comments: list[IssueComment]
    history: list[IssueHistoryEntry]
    transitions: list[IssueTransition]


@dataclass(slots=True)
class IssueListResponse(ApiModel):
    data: list[IssueSummary]


@dataclass(slots=True)
class IssueMutation(ApiModel):
    status: str
    issue: IssueDetail


@dataclass(slots=True)
class ArchiveResult(ApiModel):
    status: str
    issue_id: int
    archived_at: str


@dataclass(slots=True)
class MoveResult(ApiModel):
    status: str
    issue_id: int
    workflow_state: str
    board_position: int