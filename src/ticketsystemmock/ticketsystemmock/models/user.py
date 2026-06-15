from __future__ import annotations

from dataclasses import dataclass

from .base import ApiModel
from .group import Group
from .user_summary import UserSummary


@dataclass(slots=True)
class AuthenticatedUser(ApiModel):
    id: int
    username: str
    display_name: str
    is_staff: bool
    is_superuser: bool


@dataclass(slots=True)
class ManagedUser(ApiModel):
    id: int
    username: str
    first_name: str
    last_name: str
    display_name: str
    is_active: bool
    is_staff: bool
    is_superuser: bool
    language_preference: str
    avatar_type: str
    is_system_user: bool
    avatar_text: str
    avatar_image_url: str | None
    groups: list[Group]


@dataclass(slots=True)
class UserProfile(ApiModel):
    user: UserSummary
    language_preference: str
    language_preference_label: str
    avatar_type: str
    avatar_type_label: str
    is_system_user: bool
    avatar_text: str
    avatar_image_url: str | None
    assigned_issue_count: int
    can_edit: bool


@dataclass(slots=True)
class UserListResponse(ApiModel):
    data: list[UserSummary]


@dataclass(slots=True)
class UserProfileMutation(ApiModel):
    status: str
    profile: UserProfile


@dataclass(slots=True)
class UserMutation(ApiModel):
    status: str
    user: ManagedUser


@dataclass(slots=True)
class UserDeactivation(ApiModel):
    status: str
    user_id: int
    is_active: bool
