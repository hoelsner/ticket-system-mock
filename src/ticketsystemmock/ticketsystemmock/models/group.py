from __future__ import annotations

from dataclasses import dataclass

from .base import ApiModel
from .user_summary import UserSummary


@dataclass(slots=True)
class Group(ApiModel):
    id: int
    name: str
    description: str


@dataclass(slots=True)
class ManagedGroup(Group):
    users: list["UserSummary"]


@dataclass(slots=True)
class GroupListResponse(ApiModel):
    data: list[Group]


@dataclass(slots=True)
class GroupMutation(ApiModel):
    status: str
    group: ManagedGroup


@dataclass(slots=True)
class GroupDeletion(ApiModel):
    status: str
    group_id: int
