from __future__ import annotations

from dataclasses import dataclass

from .base import ApiModel


@dataclass(slots=True)
class Collection(ApiModel):
    id: int
    name: str
    prefix: str
    description: str


@dataclass(slots=True)
class CollectionListResponse(ApiModel):
    data: list[Collection]


@dataclass(slots=True)
class CollectionMutation(ApiModel):
    status: str
    collection: Collection