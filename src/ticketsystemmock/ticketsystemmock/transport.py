from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from .exceptions import ApiError, AuthenticationError, AuthorizationError, ConflictError, ValidationError


def normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip()
    if not normalized:
        raise ValueError("base_url is required")

    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("base_url must be an absolute http or https URL")

    return normalized.rstrip("/")


def _error_message(method: str, path: str, payload: Any) -> str:
    if isinstance(payload, dict):
        if isinstance(payload.get("error"), str):
            return payload["error"]
        if isinstance(payload.get("errors"), dict):
            return "Request validation failed."
    return f"Ticket System Mock API request {method} {path} failed."


def raise_for_response(method: str, path: str, response: httpx.Response) -> None:
    if response.is_success:
        return

    payload = None
    try:
        payload = response.json()
    except ValueError:
        payload = response.text

    message = _error_message(method, path, payload)

    if response.status_code == 401:
        raise AuthenticationError(message, status_code=response.status_code, payload=payload)
    if response.status_code == 403:
        raise AuthorizationError(message, status_code=response.status_code, payload=payload)
    if response.status_code == 409:
        raise ConflictError(message, status_code=response.status_code, payload=payload)
    if isinstance(payload, dict) and "errors" in payload:
        raise ValidationError(
            message,
            status_code=response.status_code,
            payload=payload,
            errors=payload["errors"],
        )
    raise ApiError(message, status_code=response.status_code, payload=payload)


@dataclass(slots=True)
class RequestConfig:
    params: dict[str, Any] | None = None
    json: dict[str, Any] | None = None
    data: dict[str, Any] | None = None
    files: Any = None


class SyncTransport:
    def __init__(self, base_url: str, username: str, password: str, *, timeout: float = 10.0, client=None):
        self.base_url = normalize_base_url(base_url)
        if client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                auth=(username, password),
                timeout=timeout,
            )
        else:
            client.auth = (username, password)
            self._client = client

    def request(self, method: str, path: str, *, config: RequestConfig | None = None, expect_json: bool = True):
        config = config or RequestConfig()
        response = self._client.request(
            method,
            path,
            params=config.params,
            json=config.json,
            data=config.data,
            files=config.files,
        )
        raise_for_response(method, path, response)
        return response.json() if expect_json else response.content

    def close(self) -> None:
        self._client.close()


class AsyncTransport:
    def __init__(self, base_url: str, username: str, password: str, *, timeout: float = 10.0, client=None):
        self.base_url = normalize_base_url(base_url)
        if client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=(username, password),
                timeout=timeout,
            )
        else:
            client.auth = (username, password)
            self._client = client

    async def request(
        self,
        method: str,
        path: str,
        *,
        config: RequestConfig | None = None,
        expect_json: bool = True,
    ):
        config = config or RequestConfig()
        response = await self._client.request(
            method,
            path,
            params=config.params,
            json=config.json,
            data=config.data,
            files=config.files,
        )
        raise_for_response(method, path, response)
        return response.json() if expect_json else response.content

    async def aclose(self) -> None:
        await self._client.aclose()
