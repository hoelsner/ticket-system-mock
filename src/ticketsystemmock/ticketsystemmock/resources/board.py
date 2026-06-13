from __future__ import annotations

from .. import endpoints
from ..models import BoardResponse
from ..transport import RequestConfig
from .helpers import clean_params


class SyncBoardResource:
    def __init__(self, transport):
        self._transport = transport

    def get(self, **filters) -> BoardResponse:
        response = self._transport.request("GET", endpoints.BOARD, config=RequestConfig(params=clean_params(filters)))
        return BoardResponse.from_dict(response)


class AsyncBoardResource:
    def __init__(self, transport):
        self._transport = transport

    async def get(self, **filters) -> BoardResponse:
        response = await self._transport.request(
            "GET",
            endpoints.BOARD,
            config=RequestConfig(params=clean_params(filters)),
        )
        return BoardResponse.from_dict(response)