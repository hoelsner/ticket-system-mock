from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from .base import ApiModel
from .user_summary import UserSummary


@dataclass(slots=True)
class IssueAttachment(ApiModel):
    id: int
    original_filename: str
    description: str
    content_type: str
    file_size: int
    uploaded_at: str
    file_url: str
    uploaded_by_user: UserSummary

    def resolved_file_url(self, base_url: str) -> str:
        return urljoin(f"{base_url.rstrip('/')}/", self.file_url.lstrip("/"))


@dataclass(slots=True)
class IssueAttachmentMutation(ApiModel):
    status: str
    attachment: IssueAttachment