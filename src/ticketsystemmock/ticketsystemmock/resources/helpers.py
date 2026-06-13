from __future__ import annotations

from typing import Any


def clean_params(params: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if value not in (None, "")}


def to_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = {}
    for key, value in payload.items():
        if value is None:
            continue
        if isinstance(value, bool):
            data[key] = "true" if value else "false"
            continue
        if isinstance(value, (list, tuple)):
            data[key] = [str(item) for item in value]
            continue
        data[key] = str(value)
    return data