from __future__ import annotations

from enum import StrEnum


class IssuePriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class WorkflowState(StrEnum):
    NEW = "NEW"
    TRIAGE = "TRIAGE"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING = "WAITING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class CommentVisibility(StrEnum):
    INTERNAL = "INTERNAL"


class LanguagePreference(StrEnum):
    EN = "en"
    DE = "de"


class AvatarType(StrEnum):
    INITIALS = "initials"
    IMAGE = "image"
