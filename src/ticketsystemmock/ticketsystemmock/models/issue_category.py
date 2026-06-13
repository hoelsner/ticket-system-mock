from __future__ import annotations

from dataclasses import dataclass

from .base import ApiModel


@dataclass(slots=True)
class IssueCategory(ApiModel):
    id: int
    name: str
    code: str
    description: str


@dataclass(slots=True)
class IssueCategoryListResponse(ApiModel):
    data: list[IssueCategory]


@dataclass(slots=True)
class IssueCategoryMutation(ApiModel):
    status: str
    category: IssueCategory