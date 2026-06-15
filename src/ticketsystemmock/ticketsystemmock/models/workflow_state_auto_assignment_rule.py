from __future__ import annotations

from dataclasses import dataclass

from .base import ApiModel
from .group import Group
from .user_summary import UserSummary


@dataclass(slots=True)
class WorkflowStateAutoAssignmentRule(ApiModel):
    id: int
    workflow_state: str
    workflow_state_label: str
    group: Group
    user: UserSummary | None
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(slots=True)
class WorkflowStateAutoAssignmentRuleListResponse(ApiModel):
    data: list[WorkflowStateAutoAssignmentRule]


@dataclass(slots=True)
class WorkflowStateAutoAssignmentRuleMutation(ApiModel):
    status: str
    rule: WorkflowStateAutoAssignmentRule


@dataclass(slots=True)
class WorkflowStateAutoAssignmentRuleDeletion(ApiModel):
    status: str
    rule_id: int
