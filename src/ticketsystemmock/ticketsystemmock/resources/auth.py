from __future__ import annotations

from .. import endpoints
from ..models import AuthenticatedUser


class SyncAuthResource:
    def __init__(self, transport):
        self._transport = transport

    def me(self) -> AuthenticatedUser:
        return AuthenticatedUser.from_dict(self._transport.request("GET", endpoints.AUTH_ME))


class AsyncAuthResource:
    def __init__(self, transport):
        self._transport = transport

    async def me(self) -> AuthenticatedUser:
        return AuthenticatedUser.from_dict(await self._transport.request("GET", endpoints.AUTH_ME))