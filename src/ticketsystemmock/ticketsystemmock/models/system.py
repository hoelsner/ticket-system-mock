from __future__ import annotations

from dataclasses import dataclass

from .base import ApiModel


@dataclass(slots=True)
class HealthResponse(ApiModel):
    status: str