from __future__ import annotations

from dataclasses import dataclass

from .base import ApiModel


@dataclass(slots=True)
class InstanceResetResult(ApiModel):
    status: str
    preserved_user_id: int
    deleted_counts: dict[str, int]
