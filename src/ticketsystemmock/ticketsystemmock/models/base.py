from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any, get_args, get_origin, get_type_hints


class ApiModel:
    @classmethod
    def from_dict(cls, payload: dict[str, Any]):
        type_hints = get_type_hints(cls)
        values = {}
        for field in fields(cls):
            values[field.name] = _convert_value(type_hints[field.name], payload.get(field.name))
        return cls(**values)


def _convert_list(annotation: Any, value: Any):
    item_type = get_args(annotation)[0]
    return [_convert_value(item_type, item) for item in value]


def _convert_optional(annotation: Any, value: Any):
    args = [arg for arg in get_args(annotation) if arg is not type(None)]
    if len(args) == 1:
        return _convert_value(args[0], value)
    return value


def _convert_dataclass(annotation: Any, value: Any):
    if isinstance(annotation, type) and is_dataclass(annotation):
        return annotation.from_dict(value)
    return value


def _convert_value(annotation: Any, value: Any):
    origin = get_origin(annotation)
    if value is None:
        return None

    if origin is list:
        return _convert_list(annotation, value)

    if origin is dict:
        return value

    if origin is not None:
        return _convert_optional(annotation, value)

    return _convert_dataclass(annotation, value)