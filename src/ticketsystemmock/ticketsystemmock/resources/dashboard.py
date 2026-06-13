from __future__ import annotations

from .. import endpoints
from ..models import DashboardResponse


class SyncDashboardResource:
    def __init__(self, transport):
        self._transport = transport

    def get(self) -> DashboardResponse:
        return DashboardResponse.from_dict(self._transport.request("GET", endpoints.DASHBOARD))


class AsyncDashboardResource:
    def __init__(self, transport):
        self._transport = transport

    async def get(self) -> DashboardResponse:
        return DashboardResponse.from_dict(await self._transport.request("GET", endpoints.DASHBOARD))