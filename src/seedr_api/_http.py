"""Async HTTP client wrapper around aiohttp.

Handles:
- Session lifecycle (creation, teardown)
- BasicAuth and Bearer token injection
- Centralised HTTP error → exception mapping
- JSON and binary (streaming) response helpers
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import aiohttp

from seedr_api.exceptions import (
    APIError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
)

_DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=60)


class AsyncHTTPClient:
    """Thin async wrapper around :class:`aiohttp.ClientSession`.

    Parameters
    ----------
    base_url:
        API base URL (no trailing slash).
    access_token:
        OAuth 2.0 bearer token. Takes precedence over *basic_auth*.
    basic_auth:
        ``(email, password)`` tuple for HTTP Basic Auth.
    timeout:
        Request timeout. Defaults to 60 seconds.
    """

    def __init__(
        self,
        base_url: str,
        *,
        access_token: str | None = None,
        basic_auth: tuple[str, str] | None = None,
        timeout: aiohttp.ClientTimeout = _DEFAULT_TIMEOUT,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._access_token = access_token
        self._basic_auth = basic_auth
        self._timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            auth: aiohttp.BasicAuth | None = None
            if self._basic_auth is not None:
                auth = aiohttp.BasicAuth(*self._basic_auth)
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                auth=auth,
            )
        return self._session

    async def close(self) -> None:
        """Close the underlying :class:`aiohttp.ClientSession`."""
        if self._session and not self._session.closed:
            await self._session.close()
            # Give the connector time to close cleanly.
            await asyncio.sleep(0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    def _url(self, path: str) -> str:
        return f"{self._base_url}/{path.lstrip('/')}"

    @staticmethod
    async def _raise_for_status(response: aiohttp.ClientResponse) -> None:
        """Map HTTP errors to domain-specific exceptions."""
        if response.status < 400:
            return

        try:
            body: dict[str, Any] = await response.json(content_type=None)
            message: str = body.get(
                "error", body.get("message", response.reason or "Unknown error")
            )
        except (ValueError, aiohttp.ContentTypeError):
            message = response.reason or "Unknown error"

        status = response.status

        if status == 401:
            raise AuthenticationError(message, status_code=status)
        if status == 403:
            raise ForbiddenError(message, status_code=status)
        if status == 404:
            raise NotFoundError(message, status_code=status)
        if status == 429:
            retry_after: int | None = None
            ra = response.headers.get("Retry-After")
            if ra is not None:
                try:
                    retry_after = int(ra)
                except ValueError:
                    pass
            raise RateLimitError(message, status_code=status, retry_after=retry_after)
        if status >= 500:
            raise ServerError(message, status_code=status)
        raise APIError(message, status_code=status)

    # ------------------------------------------------------------------
    # Public request methods
    # ------------------------------------------------------------------

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        """Perform a GET request and return the parsed JSON body."""
        session = self._get_session()
        async with session.get(
            self._url(path),
            headers=self._build_headers(),
            params=params,
        ) as resp:
            await self._raise_for_status(resp)
            return await resp.json(content_type=None)

    async def post(
        self,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        form_data: aiohttp.FormData | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Perform a POST request and return the parsed JSON body."""
        session = self._get_session()
        body: aiohttp.FormData | dict[str, Any] | None = (
            form_data if form_data is not None else data
        )
        async with session.post(
            self._url(path),
            headers=self._build_headers(),
            data=body,
            params=params,
        ) as resp:
            await self._raise_for_status(resp)
            if resp.status == 204:
                return {}
            return await resp.json(content_type=None)

    async def delete(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        """Perform a DELETE request and return the parsed JSON body."""
        session = self._get_session()
        async with session.delete(
            self._url(path),
            headers=self._build_headers(),
            params=params,
        ) as resp:
            await self._raise_for_status(resp)
            if resp.status == 204:
                return {}
            return await resp.json(content_type=None)

    async def get_bytes(
        self, path: str, *, params: dict[str, Any] | None = None
    ) -> bytes:
        """Perform a GET request and return the raw response body as bytes."""
        session = self._get_session()
        async with session.get(
            self._url(path),
            headers={**self._build_headers(), "Accept": "*/*"},
            params=params,
            allow_redirects=True,
        ) as resp:
            await self._raise_for_status(resp)
            return await resp.read()

    async def stream(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        chunk_size: int = 8192,
    ) -> AsyncGenerator[bytes, None]:
        """Stream a GET response as an async generator of byte chunks.

        Usage::

            async for chunk in client.stream("/download/file/123"):
                file.write(chunk)
        """
        session = self._get_session()
        async with session.get(
            self._url(path),
            headers={**self._build_headers(), "Accept": "*/*"},
            params=params,
            allow_redirects=True,
        ) as resp:
            await self._raise_for_status(resp)
            async for chunk in resp.content.iter_chunked(chunk_size):
                if chunk:
                    yield chunk

    def update_token(self, access_token: str) -> None:
        """Replace the bearer token (e.g. after a token refresh)."""
        self._access_token = access_token
