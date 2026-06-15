from __future__ import annotations

from .resources import (
    AsyncAdminResource,
    AsyncAttachmentsResource,
    AsyncAuthResource,
    AsyncBoardResource,
    AsyncCommentsResource,
    AsyncDashboardResource,
    AsyncIssuesResource,
    AsyncProfilesResource,
    AsyncReferenceResource,
    AsyncSystemResource,
    SyncAdminResource,
    SyncAttachmentsResource,
    SyncAuthResource,
    SyncBoardResource,
    SyncCommentsResource,
    SyncDashboardResource,
    SyncIssuesResource,
    SyncProfilesResource,
    SyncReferenceResource,
    SyncSystemResource,
)
from .transport import AsyncTransport, SyncTransport


class TicketSystemClient:
    def __init__(self, base_url: str, username: str, password: str, *, timeout: float = 10.0, client=None):
        self._transport = SyncTransport(base_url, username, password, timeout=timeout, client=client)
        self.system = SyncSystemResource(self._transport)
        self.auth = SyncAuthResource(self._transport)
        self.profiles = SyncProfilesResource(self._transport)
        self.reference = SyncReferenceResource(self._transport)
        self.board = SyncBoardResource(self._transport)
        self.dashboard = SyncDashboardResource(self._transport)
        self.issues = SyncIssuesResource(self._transport)
        self.comments = SyncCommentsResource(self.issues)
        self.attachments = SyncAttachmentsResource(self.issues)
        self.admin = SyncAdminResource(self._transport)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


class AsyncTicketSystemClient:
    def __init__(self, base_url: str, username: str, password: str, *, timeout: float = 10.0, client=None):
        self._transport = AsyncTransport(base_url, username, password, timeout=timeout, client=client)
        self.system = AsyncSystemResource(self._transport)
        self.auth = AsyncAuthResource(self._transport)
        self.profiles = AsyncProfilesResource(self._transport)
        self.reference = AsyncReferenceResource(self._transport)
        self.board = AsyncBoardResource(self._transport)
        self.dashboard = AsyncDashboardResource(self._transport)
        self.issues = AsyncIssuesResource(self._transport)
        self.comments = AsyncCommentsResource(self.issues)
        self.attachments = AsyncAttachmentsResource(self.issues)
        self.admin = AsyncAdminResource(self._transport)

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.aclose()
        return False
