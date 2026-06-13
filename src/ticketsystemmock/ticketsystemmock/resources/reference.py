from __future__ import annotations

from .. import endpoints
from ..models import (
    CollectionListResponse,
    CollectionMutation,
    GroupListResponse,
    IssueCategoryListResponse,
    IssueCategoryMutation,
    UserListResponse,
)
from ..transport import RequestConfig
from .helpers import clean_params


class SyncReferenceResource:
    def __init__(self, transport):
        self._transport = transport

    def list_groups(self):
        return GroupListResponse.from_dict(self._transport.request("GET", endpoints.GROUPS)).data

    def list_users(self, *, group_id: int | None = None):
        response = self._transport.request(
            "GET",
            endpoints.USERS,
            config=RequestConfig(params=clean_params({"group_id": group_id})),
        )
        return UserListResponse.from_dict(response).data

    def list_collections(self):
        return CollectionListResponse.from_dict(self._transport.request("GET", endpoints.COLLECTIONS)).data

    def list_categories(self):
        return IssueCategoryListResponse.from_dict(self._transport.request("GET", endpoints.CATEGORIES)).data

    def create_collection(self, **payload) -> CollectionMutation:
        response = self._transport.request("POST", endpoints.COLLECTIONS, config=RequestConfig(json=payload))
        return CollectionMutation.from_dict(response)

    def update_collection(self, collection_id: int, **payload) -> CollectionMutation:
        response = self._transport.request(
            "PUT",
            endpoints.collection_detail(collection_id),
            config=RequestConfig(json=payload),
        )
        return CollectionMutation.from_dict(response)

    def create_category(self, **payload) -> IssueCategoryMutation:
        response = self._transport.request("POST", endpoints.CATEGORIES, config=RequestConfig(json=payload))
        return IssueCategoryMutation.from_dict(response)

    def update_category(self, category_id: int, **payload) -> IssueCategoryMutation:
        response = self._transport.request(
            "PUT",
            endpoints.category_detail(category_id),
            config=RequestConfig(json=payload),
        )
        return IssueCategoryMutation.from_dict(response)


class AsyncReferenceResource:
    def __init__(self, transport):
        self._transport = transport

    async def list_groups(self):
        return GroupListResponse.from_dict(await self._transport.request("GET", endpoints.GROUPS)).data

    async def list_users(self, *, group_id: int | None = None):
        response = await self._transport.request(
            "GET",
            endpoints.USERS,
            config=RequestConfig(params=clean_params({"group_id": group_id})),
        )
        return UserListResponse.from_dict(response).data

    async def list_collections(self):
        return CollectionListResponse.from_dict(await self._transport.request("GET", endpoints.COLLECTIONS)).data

    async def list_categories(self):
        return IssueCategoryListResponse.from_dict(await self._transport.request("GET", endpoints.CATEGORIES)).data

    async def create_collection(self, **payload) -> CollectionMutation:
        response = await self._transport.request("POST", endpoints.COLLECTIONS, config=RequestConfig(json=payload))
        return CollectionMutation.from_dict(response)

    async def update_collection(self, collection_id: int, **payload) -> CollectionMutation:
        response = await self._transport.request(
            "PUT",
            endpoints.collection_detail(collection_id),
            config=RequestConfig(json=payload),
        )
        return CollectionMutation.from_dict(response)

    async def create_category(self, **payload) -> IssueCategoryMutation:
        response = await self._transport.request("POST", endpoints.CATEGORIES, config=RequestConfig(json=payload))
        return IssueCategoryMutation.from_dict(response)

    async def update_category(self, category_id: int, **payload) -> IssueCategoryMutation:
        response = await self._transport.request(
            "PUT",
            endpoints.category_detail(category_id),
            config=RequestConfig(json=payload),
        )
        return IssueCategoryMutation.from_dict(response)