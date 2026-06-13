from __future__ import annotations

from .. import endpoints
from ..models import HealthResponse


class SyncSystemResource:
    def __init__(self, transport):
        self._transport = transport

    def health(self) -> HealthResponse:
        return HealthResponse.from_dict(self._transport.request("GET", endpoints.HEALTH))


class AsyncSystemResource:
    def __init__(self, transport):
        self._transport = transport

    async def health(self) -> HealthResponse:
        return HealthResponse.from_dict(await self._transport.request("GET", endpoints.HEALTH))