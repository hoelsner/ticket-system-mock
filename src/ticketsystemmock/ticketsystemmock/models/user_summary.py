from __future__ import annotations

from dataclasses import dataclass

from .base import ApiModel


@dataclass(slots=True)
class UserSummary(ApiModel):
    id: int
    username: str
    display_name: str
    avatar_type: str
    is_system_user: bool
    avatar_text: str
    avatar_image_url: str | None
