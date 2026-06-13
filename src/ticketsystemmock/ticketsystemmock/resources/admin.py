from __future__ import annotations

from .. import endpoints
from ..models import GroupDeletion, GroupMutation, ManagedGroup, ManagedUser, UserDeactivation, UserMutation
from ..transport import RequestConfig


class SyncAdminUsersResource:
    def __init__(self, transport):
        self._transport = transport

    def create(self, **payload) -> UserMutation:
        return UserMutation.from_dict(self._transport.request("POST", endpoints.USERS, config=RequestConfig(json=payload)))

    def get(self, user_id: int) -> ManagedUser:
        return ManagedUser.from_dict(self._transport.request("GET", endpoints.user_detail(user_id)))

    def update(self, user_id: int, **payload) -> UserMutation:
        return UserMutation.from_dict(
            self._transport.request("PUT", endpoints.user_detail(user_id), config=RequestConfig(json=payload))
        )

    def deactivate(self, user_id: int) -> UserDeactivation:
        return UserDeactivation.from_dict(self._transport.request("DELETE", endpoints.user_detail(user_id)))


class AsyncAdminUsersResource:
    def __init__(self, transport):
        self._transport = transport

    async def create(self, **payload) -> UserMutation:
        return UserMutation.from_dict(
            await self._transport.request("POST", endpoints.USERS, config=RequestConfig(json=payload))
        )

    async def get(self, user_id: int) -> ManagedUser:
        return ManagedUser.from_dict(await self._transport.request("GET", endpoints.user_detail(user_id)))

    async def update(self, user_id: int, **payload) -> UserMutation:
        return UserMutation.from_dict(
            await self._transport.request("PUT", endpoints.user_detail(user_id), config=RequestConfig(json=payload))
        )

    async def deactivate(self, user_id: int) -> UserDeactivation:
        return UserDeactivation.from_dict(await self._transport.request("DELETE", endpoints.user_detail(user_id)))


class SyncAdminGroupsResource:
    def __init__(self, transport):
        self._transport = transport

    def create(self, **payload) -> GroupMutation:
        return GroupMutation.from_dict(self._transport.request("POST", endpoints.GROUPS, config=RequestConfig(json=payload)))

    def get(self, group_id: int) -> ManagedGroup:
        return ManagedGroup.from_dict(self._transport.request("GET", endpoints.group_detail(group_id)))

    def update(self, group_id: int, **payload) -> GroupMutation:
        return GroupMutation.from_dict(
            self._transport.request("PUT", endpoints.group_detail(group_id), config=RequestConfig(json=payload))
        )

    def delete(self, group_id: int) -> GroupDeletion:
        return GroupDeletion.from_dict(self._transport.request("DELETE", endpoints.group_detail(group_id)))


class AsyncAdminGroupsResource:
    def __init__(self, transport):
        self._transport = transport

    async def create(self, **payload) -> GroupMutation:
        return GroupMutation.from_dict(
            await self._transport.request("POST", endpoints.GROUPS, config=RequestConfig(json=payload))
        )

    async def get(self, group_id: int) -> ManagedGroup:
        return ManagedGroup.from_dict(await self._transport.request("GET", endpoints.group_detail(group_id)))

    async def update(self, group_id: int, **payload) -> GroupMutation:
        return GroupMutation.from_dict(
            await self._transport.request("PUT", endpoints.group_detail(group_id), config=RequestConfig(json=payload))
        )

    async def delete(self, group_id: int) -> GroupDeletion:
        return GroupDeletion.from_dict(await self._transport.request("DELETE", endpoints.group_detail(group_id)))


class SyncAdminResource:
    def __init__(self, transport):
        self.users = SyncAdminUsersResource(transport)
        self.groups = SyncAdminGroupsResource(transport)


class AsyncAdminResource:
    def __init__(self, transport):
        self.users = AsyncAdminUsersResource(transport)
        self.groups = AsyncAdminGroupsResource(transport)