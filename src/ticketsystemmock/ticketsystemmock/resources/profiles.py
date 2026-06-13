from __future__ import annotations

from .. import endpoints
from ..models import UserProfile, UserProfileMutation
from ..transport import RequestConfig
from .helpers import to_data


class SyncProfilesResource:
    def __init__(self, transport):
        self._transport = transport

    def me(self) -> UserProfile:
        return UserProfile.from_dict(self._transport.request("GET", endpoints.PROFILE_ME))

    def get(self, username: str) -> UserProfile:
        return UserProfile.from_dict(self._transport.request("GET", endpoints.user_profile(username)))

    def update(self, **payload) -> UserProfileMutation:
        response = self._transport.request(
            "PUT",
            endpoints.PROFILE_ME,
            config=RequestConfig(data=to_data(payload)),
        )
        return UserProfileMutation.from_dict(response)


class AsyncProfilesResource:
    def __init__(self, transport):
        self._transport = transport

    async def me(self) -> UserProfile:
        return UserProfile.from_dict(await self._transport.request("GET", endpoints.PROFILE_ME))

    async def get(self, username: str) -> UserProfile:
        return UserProfile.from_dict(await self._transport.request("GET", endpoints.user_profile(username)))

    async def update(self, **payload) -> UserProfileMutation:
        response = await self._transport.request(
            "PUT",
            endpoints.PROFILE_ME,
            config=RequestConfig(data=to_data(payload)),
        )
        return UserProfileMutation.from_dict(response)