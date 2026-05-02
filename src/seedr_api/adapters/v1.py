"""V1 Adapter — uses resource.php POST API at www.seedr.cc/oauth_test/."""

from __future__ import annotations

import json
from typing import Any

import aiohttp

from seedr_api.exceptions import (
    APIError,
    AuthenticationError,
    ForbiddenError,
    InsufficientSpaceError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TokenExpiredError,
)
from seedr_api.models.v1.account import V1AccountSettings, V1Device, V1MemoryBandwidth
from seedr_api.models.v1.auth import V1DeviceCode, V1RefreshToken, V1TokenResponse
from seedr_api.models.v1.filesystem import V1FolderContents
from seedr_api.models.v1.tasks import (
    V1AddFolderResult,
    V1AddTorrentResult,
    V1DeleteResult,
    V1DeleteWishlistResult,
    V1FetchFileResult,
    V1RenameResult,
    V1SearchResult,
    V1TorrentProgress,
)

_V1_TOKEN_URL = "https://www.seedr.cc/oauth_test/token.php"
_V1_RESOURCE_URL = "https://www.seedr.cc/oauth_test/resource.php"
_V1_DEVICE_CODE_URL = "https://www.seedr.cc/api/device/code"
_V1_DEVICE_AUTHORIZE_URL = "https://www.seedr.cc/api/device/authorize"

_CREDENTIAL_CLIENT_ID = "seedr_chrome"  # password login + token refresh
_DEVICE_CLIENT_ID = "seedr_xbmc"  # device code + device authorize


def _check_v1_error(data: dict[str, Any]) -> None:
    """Raise the appropriate exception for a V1 error payload.

    Covers both the ``error`` field convention and the ``status_code`` /
    ``reason_phrase`` convention used by some V1 domain-error responses.
    """
    error = data.get("error")

    if error == "expired_token":
        raise TokenExpiredError("V1 access token has expired", status_code=401)
    if error in ("access_denied", "invalid_token"):
        # invalid_token: token revoked; access_denied: auth refused
        raise AuthenticationError(
            data.get("error_description") or error, status_code=401
        )
    if error == "unknown_func":
        func = data.get("func", "unknown")
        raise APIError(f"Unknown function: {func}", status_code=404)

    if data.get("result") is False:
        raise APIError(data.get("error") or "Unknown V1 error")

    # Some V1 endpoints return {status_code, reason_phrase} for domain errors
    # (e.g. 409 "Name already taken") instead of result:false
    body_status = data.get("status_code")
    if isinstance(body_status, int) and body_status >= 400:
        reason = str(data.get("reason_phrase", "API error"))
        if body_status == 401:
            raise AuthenticationError(reason, status_code=401)
        if body_status == 403:
            raise ForbiddenError(reason, status_code=403)
        if body_status == 404:
            raise NotFoundError(reason, status_code=404)
        if body_status == 413:
            raise InsufficientSpaceError(reason, status_code=413)
        if body_status == 429:
            raise RateLimitError(reason, status_code=429)
        if body_status >= 500:
            raise ServerError(reason, status_code=body_status)
        raise APIError(reason, status_code=body_status)


def _check_token_error(data: dict[str, Any]) -> None:
    """Raise the appropriate exception for a token-endpoint error payload.

    token.php uses OAuth 2.0 error conventions:
    ``{"error": "invalid_grant", "error_description": "..."}``
    """
    error = data.get("error")
    if not error:
        return

    description: str = data.get("error_description") or str(error)

    if error in ("invalid_grant", "invalid_client", "invalid_credentials"):
        raise AuthenticationError(description, status_code=401)
    if error == "expired_token":
        raise TokenExpiredError(description, status_code=401)
    if error == "access_denied":
        raise AuthenticationError(description, status_code=401)
    # Catch-all for any other OAuth error codes
    raise APIError(f"{error}: {description}")


def _raise_for_http_status(status: int, data: dict[str, Any]) -> None:
    """Raise a domain exception for non-2xx HTTP responses."""
    if status < 400:
        return

    reason: str = str(
        data.get("reason_phrase")
        or data.get("error_description")
        or data.get("error")
        or data.get("message")
        or "HTTP error"
    )

    if status == 401:
        _check_v1_error(data)  # prefer specific error type from body
        raise AuthenticationError(reason, status_code=401)
    if status == 403:
        raise ForbiddenError(reason, status_code=403)
    if status == 404:
        _check_v1_error(data)
        raise NotFoundError(reason, status_code=404)
    if status == 413:
        wt = data.get("wt") or data.get("wishlist_item")
        raise InsufficientSpaceError(reason, status_code=413, wishlist_item=wt)
    if status == 429:
        raise RateLimitError(reason, status_code=429)
    if status >= 500:
        raise ServerError(reason, status_code=status)
    raise APIError(reason, status_code=status)


class V1Adapter:
    """Adapter that communicates with the V1 (resource.php) API.

    Parameters
    ----------
    access_token:
        OAuth access token to include in each resource.php POST.
    timeout:
        Per-request timeout in seconds.
    """

    def __init__(
        self,
        access_token: str,
        *,
        timeout: float = 60.0,
    ) -> None:
        self._access_token = access_token
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session

    async def close(self) -> None:
        """Close the underlying aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def update_token(self, access_token: str) -> None:
        """Update the access token (called after auto-refresh)."""
        self._access_token = access_token

    # ------------------------------------------------------------------
    # Raw helpers
    # ------------------------------------------------------------------

    async def _post_resource(self, func: str, **kwargs: Any) -> dict[str, Any]:
        """POST to resource.php, raise on any V1 or HTTP error, return parsed JSON."""
        params: dict[str, Any] = {
            "func": func,
            "access_token": self._access_token,
            **kwargs,
        }
        session = self._get_session()
        async with session.post(
            _V1_RESOURCE_URL,
            data=params,
            headers={"Accept": "application/json"},
        ) as resp:
            data: dict[str, Any] = await resp.json(content_type=None)
            _raise_for_http_status(resp.status, data)
            _check_v1_error(data)
            return data

    async def _get_raw(
        self, url: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """GET a JSON endpoint, raising on HTTP errors."""
        session = self._get_session()
        async with session.get(
            url,
            params=params,
            headers={"Accept": "application/json"},
        ) as resp:
            data: dict[str, Any] = await resp.json(content_type=None)
            _raise_for_http_status(resp.status, data)
            return data

    async def _post_token(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST to the V1 token endpoint, raising on auth errors."""
        session = self._get_session()
        async with session.post(
            _V1_TOKEN_URL,
            data=payload,
            headers={"Accept": "application/json"},
        ) as resp:
            data: dict[str, Any] = await resp.json(content_type=None)
            _raise_for_http_status(resp.status, data)
            _check_token_error(data)
            return data

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    async def login(
        self,
        username: str,
        password: str,
        *,
        client_id: str = _CREDENTIAL_CLIENT_ID,
    ) -> V1TokenResponse:
        """Authenticate with username/password.

        Raises
        ------
        AuthenticationError
            If credentials are invalid.
        """
        data = await self._post_token(
            {
                "grant_type": "password",
                "client_id": client_id,
                "username": username,
                "password": password,
            }
        )
        return V1TokenResponse.model_validate(data)

    async def refresh_token(
        self,
        refresh_token: str,
        client_id: str = _CREDENTIAL_CLIENT_ID,
    ) -> V1RefreshToken:
        """Refresh an access token. Note: V1 does NOT return a new refresh_token.

        Raises
        ------
        AuthenticationError
            If the refresh token is invalid or expired.
        """
        data = await self._post_token(
            {
                "grant_type": "refresh_token",
                "client_id": client_id,
                "refresh_token": refresh_token,
            }
        )
        return V1RefreshToken.model_validate(data)

    async def get_device_code(
        self,
        client_id: str = _DEVICE_CLIENT_ID,
    ) -> V1DeviceCode:
        """Request a device authorization code.

        Raises
        ------
        APIError
            If the client_id is invalid or the request fails.
        """
        data = await self._get_raw(
            _V1_DEVICE_CODE_URL,
            params={"client_id": client_id},
        )
        _check_token_error(data)
        return V1DeviceCode.model_validate(data)

    async def authorize_device(
        self,
        device_code: str,
        client_id: str = _DEVICE_CLIENT_ID,
    ) -> V1TokenResponse:
        """Poll device authorization — returns token on success.

        Raises
        ------
        AuthenticationError
            If ``access_denied`` is returned.
        TokenExpiredError
            If the device code has expired.
        APIError
            If authorization is still pending (``authorization_pending``) or
            the client should slow its polling (``slow_down``).
        """
        data = await self._get_raw(
            _V1_DEVICE_AUTHORIZE_URL,
            params={"device_code": device_code, "client_id": client_id},
        )
        error = data.get("error")
        if error == "authorization_pending":
            raise APIError(
                "Authorization pending — user has not yet approved", status_code=202
            )
        if error == "slow_down":
            raise APIError("Polling too fast — slow down", status_code=429)
        if error == "expired_token":
            raise TokenExpiredError("Device code has expired", status_code=401)
        if error == "access_denied":
            raise AuthenticationError("User denied authorization", status_code=401)
        if error:
            raise APIError(f"Device auth error: {error}")
        return V1TokenResponse.model_validate(data)

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------

    async def get_settings(self) -> V1AccountSettings:
        """Return full account settings.

        Raises
        ------
        AuthenticationError / TokenExpiredError
            If the access token is invalid or expired.
        """
        data = await self._post_resource("get_settings")
        return V1AccountSettings.model_validate(data)

    async def get_memory_bandwidth(self) -> V1MemoryBandwidth:
        """Return memory and bandwidth quota."""
        data = await self._post_resource("get_memory_bandwidth")
        return V1MemoryBandwidth.model_validate(data)

    async def get_devices(self) -> list[V1Device]:
        """Return registered device list."""
        data = await self._post_resource("get_devices")
        devices: list[Any] = data.get("devices", [])
        return [V1Device.model_validate(d) for d in devices]

    # ------------------------------------------------------------------
    # Filesystem
    # ------------------------------------------------------------------

    async def list_contents(
        self,
        folder_id: int | str = 0,
        content_type: str = "folder",
    ) -> V1FolderContents:
        """List contents of a folder.

        Raises
        ------
        NotFoundError
            If the folder does not exist.
        """
        data = await self._post_resource(
            "list_contents",
            content_type=content_type,
            content_id=str(folder_id),
        )
        return V1FolderContents.model_validate(data)

    async def get_folder(self, folder_id: int) -> V1FolderContents:
        """Get folder metadata (alias for list_contents)."""
        return await self.list_contents(folder_id)

    async def get_file(self, file_id: int) -> V1FetchFileResult:
        """Get a download URL for a file.

        Raises
        ------
        NotFoundError
            If the file does not exist.
        """
        data = await self._post_resource("fetch_file", folder_file_id=str(file_id))
        return V1FetchFileResult.model_validate(data)

    async def create_folder(
        self, name: str, parent_id: int | None = None
    ) -> V1AddFolderResult:
        """Create a new folder. V1 does not support parent_id.

        Raises
        ------
        APIError
            If a folder with this name already exists or the request fails.
        """
        data = await self._post_resource("add_folder", name=name)
        return V1AddFolderResult.model_validate(data)

    async def rename(
        self,
        new_name: str,
        *,
        folder_id: int | None = None,
        folder_file_id: int | None = None,
    ) -> V1RenameResult:
        """Rename a folder or file.

        Raises
        ------
        APIError
            If the name is already taken (409) or neither ID is provided.
        NotFoundError
            If the folder or file does not exist.
        """
        kwargs: dict[str, Any] = {"rename_to": new_name}
        if folder_id is not None:
            kwargs["folder_id"] = str(folder_id)
        elif folder_file_id is not None:
            kwargs["folder_file_id"] = str(folder_file_id)
        data = await self._post_resource("rename", **kwargs)
        return V1RenameResult.model_validate(data)

    async def delete(self, items: list[dict[str, Any]]) -> V1DeleteResult:
        """Delete folders, files, or torrents.

        Parameters
        ----------
        items:
            List of ``{"type": "folder"|"folder_file"|"torrent", "id": int}``.

        Raises
        ------
        NotFoundError
            If an item does not exist.
        """
        data = await self._post_resource(
            "delete",
            delete_arr=json.dumps(items),
        )
        return V1DeleteResult.model_validate(data)

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    async def get_tasks(self) -> list[Any]:
        """Return active tasks from list_contents (V1 has no dedicated tasks endpoint)."""
        contents = await self.list_contents(0)
        return list(contents.tasks)

    async def get_task(self, task_id: int) -> Any:
        """Not available in V1 — raises NotImplementedError."""
        raise NotImplementedError("get_task is only supported via the V2 adapter.")

    async def delete_task(self, task_id: int) -> Any:
        """Delete a task (torrent) by ID."""
        return await self.delete([{"type": "torrent", "id": task_id}])

    async def add_task(
        self,
        *,
        torrent_magnet: str | None = None,
        wishlist_id: int | None = None,
        folder_id: int | None = None,
    ) -> V1AddTorrentResult:
        """Add a torrent task.

        Raises
        ------
        InsufficientSpaceError
            If the account has no space; the torrent is auto-added to wishlist.
        APIError
            For other failures.
        """
        kwargs: dict[str, Any] = {}
        if torrent_magnet is not None:
            kwargs["torrent_magnet"] = torrent_magnet
        if wishlist_id is not None:
            kwargs["wishlist_id"] = str(wishlist_id)
        if folder_id is not None:
            kwargs["folder_id"] = str(folder_id)
        data = await self._post_resource("add_torrent", **kwargs)
        return V1AddTorrentResult.model_validate(data)

    # ------------------------------------------------------------------
    # Downloads
    # ------------------------------------------------------------------

    async def get_file_url(self, file_id: int) -> V1FetchFileResult:
        """Return download URL for a file.

        Raises
        ------
        NotFoundError
            If the file does not exist.
        """
        data = await self._post_resource("fetch_file", folder_file_id=str(file_id))
        return V1FetchFileResult.model_validate(data)

    async def get_file_bytes(self, file_id: int) -> bytes:
        """Not supported in V1 — raises NotImplementedError."""
        raise NotImplementedError(
            "Direct file download is only supported via the V2 API."
        )

    async def init_archive(
        self,
        uuid: str,
        folder_id: int,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Not supported in V1 — raises NotImplementedError."""
        raise NotImplementedError("Archive init is only supported via the V2 API.")

    async def create_archive(
        self,
        items: list[dict[str, Any]],
        folder_id: int | None = None,
    ) -> dict[str, Any]:
        """Not available in V1 (func=create_empty_archive returns unknown_func)."""
        raise NotImplementedError("create_archive is not supported via the V1 API.")

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search_files(self, query: str) -> V1SearchResult:
        """Search files and folders by query string."""
        data = await self._post_resource("search_files", search_query=query)
        return V1SearchResult.model_validate(data)

    async def scan_page(self, url: str) -> dict[str, Any]:
        """Not available in V1 (func=scan_page returns unknown_func)."""
        raise NotImplementedError("scan_page is not supported via the V1 API.")

    # ------------------------------------------------------------------
    # Presentations / Subtitles — V1 stubs
    # ------------------------------------------------------------------

    async def get_folder_presentations(self, folder_id: int) -> dict[str, Any]:
        """Not supported in V1 — returns empty payload."""
        return {"files": [], "total_files": 0}

    async def get_subtitles(self, file_id: int) -> dict[str, Any]:
        """Not supported in V1 — returns empty payload."""
        return {"subtitles": [], "file_subtitles": [], "folder_file_subtitles": []}

    # ------------------------------------------------------------------
    # Wishlist
    # ------------------------------------------------------------------

    async def get_wishlist(self) -> list[Any]:
        """Return wishlist items from account settings."""
        settings = await self.get_settings()
        return list(settings.account.wishlist) if settings.account else []

    async def delete_wishlist_item(self, wishlist_id: int) -> V1DeleteWishlistResult:
        """Delete a wishlist item.

        Raises
        ------
        NotFoundError
            If the wishlist item does not exist.
        APIError
            For other failures.
        """
        # V1 resource.php uses func=remove_wishlist with param id= (not delete_wishlist)
        data = await self._post_resource("remove_wishlist", id=str(wishlist_id))
        return V1DeleteWishlistResult.model_validate(data)

    # ------------------------------------------------------------------
    # Account modification — not available in V1
    # ------------------------------------------------------------------

    async def modify_account_name(
        self,
        first_name: str,
        last_name: str,
    ) -> dict[str, Any]:
        """Not available in V1 (func=user_account_modify returns unknown_func)."""
        raise NotImplementedError(
            "modify_account_name is not supported via the V1 API."
        )

    async def modify_account_password(
        self,
        current_password: str,
        new_password: str,
    ) -> dict[str, Any]:
        """Not available in V1 (func=user_account_modify returns unknown_func)."""
        raise NotImplementedError(
            "modify_account_password is not supported via the V1 API."
        )

    # ------------------------------------------------------------------
    # Torrent progress
    # ------------------------------------------------------------------

    async def get_torrent_progress(self, progress_url: str) -> V1TorrentProgress:
        """Fetch live download progress for an active torrent.

        Parameters
        ----------
        progress_url:
            The ``progress_url`` field from a torrent entry in
            :meth:`list_contents` (e.g. ``torrent.progress_url``).

        Returns
        -------
        V1TorrentProgress
            Download progress including percentage, speed, and ETA.

        Raises
        ------
        APIError
            If the request fails.
        """
        data = await self._get_raw(
            progress_url,
            params={"access_token": self._access_token},
        )
        return V1TorrentProgress.model_validate(data)
