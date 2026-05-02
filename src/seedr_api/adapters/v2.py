"""V2 Adapter — uses REST API at v2.seedr.cc/api/v0.1/p with Bearer OAuth."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
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
from seedr_api.models.v2.account import (
    V2AccountInfo,
    V2AccountSettings,
    V2Quota,
    V2WishlistItem,
)
from seedr_api.models.v2.auth import V2DeviceCode, V2TokenResponse
from seedr_api.models.v2.downloads import V2ArchiveInit, V2DownloadURL
from seedr_api.models.v2.filesystem import (
    V2AddFolderResult,
    V2DeleteResult,
    V2FileInfo,
    V2FolderContents,
)
from seedr_api.models.v2.presentations import V2FolderPresentations
from seedr_api.models.v2.subtitles import V2SubtitlesList
from seedr_api.models.v2.tasks import (
    V2AddTaskResult,
    V2SingleTaskResponse,
    V2TasksResponse,
)

_V2_BASE = "https://v2.seedr.cc/api/v0.1/p"

_DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=60)


def _check_v2_error(data: dict[str, Any], status: int) -> None:
    """Raise appropriate exception for a V2 error payload."""
    reason = data.get("reason_phrase", data.get("error", ""))
    message = data.get("message", reason) or reason

    if status == 401:
        if "expired" in str(reason).lower() or "expired" in str(message).lower():
            raise TokenExpiredError(message or "Token expired", status_code=401)
        raise AuthenticationError(message or "Unauthorized", status_code=401)
    if status == 403:
        raise ForbiddenError(message or "Forbidden", status_code=403)
    if status == 404:
        raise NotFoundError(str(reason or message or "Not Found"), status_code=404)
    if status == 413:
        wt = data.get("wt")
        raise InsufficientSpaceError(
            str(reason or "Not enough space"),
            status_code=413,
            wishlist_item=wt,
        )
    if status >= 500:
        raise ServerError(message or "Server error", status_code=status)
    raise APIError(message or "API error", status_code=status)


class V2Adapter:
    """Adapter that communicates with the V2 REST API.

    Parameters
    ----------
    access_token:
        OAuth 2.0 bearer token or Personal Access Token (PAT).
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

    def _build_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            # Exclude brotli — aiohttp can't decompress br responses
            "Accept-Encoding": "gzip, deflate",
            "Authorization": f"Bearer {self._access_token}",
        }

    def _url(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        return f"{_V2_BASE}/{path.lstrip('/')}"

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Any:
        """Execute an HTTP request and return parsed JSON."""
        session = self._get_session()
        async with session.request(
            method,
            self._url(path),
            headers=self._build_headers(),
            **kwargs,
        ) as resp:
            if resp.status < 400:
                if resp.status == 204:
                    return {}
                return await resp.json(content_type=None)
            try:
                body: dict[str, Any] = await resp.json(content_type=None)
            except Exception:
                body = {}
            if resp.status == 429:
                retry_after: int | None = None
                ra = resp.headers.get("Retry-After")
                if ra is not None:
                    try:
                        retry_after = int(ra)
                    except ValueError:
                        pass
                raise RateLimitError(
                    body.get("message", "Rate limit exceeded"),
                    status_code=429,
                    retry_after=retry_after,
                )
            _check_v2_error(body, resp.status)

    async def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def _post(
        self,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        form_data: aiohttp.FormData | None = None,
    ) -> Any:
        if form_data is not None:
            return await self._request("POST", path, data=form_data)
        if json_body is not None:
            return await self._request("POST", path, json=json_body)
        return await self._request("POST", path, data=data)

    async def _put(self, path: str, *, json_body: dict[str, Any] | None = None) -> Any:
        return await self._request("PUT", path, json=json_body)

    async def _delete(self, path: str, *, data: dict[str, Any] | None = None) -> Any:
        return await self._request("DELETE", path, data=data)

    # ------------------------------------------------------------------
    # Auth (V2 OAuth token operations)
    # ------------------------------------------------------------------

    async def login(self, username: str, password: str) -> V2TokenResponse:
        """Login is not supported directly via V2 OAuth (requires CAPTCHA).

        Use V1Adapter.login() and convert the token instead.
        """
        raise NotImplementedError(
            "V2 login requires Turnstile CAPTCHA. Use V1Adapter.login() instead."
        )

    async def oauth_token(self, data: dict[str, Any]) -> V2TokenResponse:
        """Exchange OAuth credentials for a token."""
        raw = await self._post("/oauth/token", data=data)
        return V2TokenResponse.model_validate(raw)

    async def refresh_token(
        self,
        refresh_token: str,
        client_id: str,
        client_secret: str | None = None,
    ) -> V2TokenResponse:
        """Refresh an access token."""
        payload: dict[str, Any] = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh_token,
        }
        if client_secret is not None:
            payload["client_secret"] = client_secret
        raw = await self._post("/oauth/token", data=payload)
        return V2TokenResponse.model_validate(raw)

    async def get_device_code(
        self,
        client_id: str,
        client_secret: str | None = None,
        scope: str = "profile account.read account.write files.read files.write tasks.read tasks.write",
    ) -> V2DeviceCode:
        """Request a device code."""
        payload: dict[str, Any] = {"client_id": client_id, "scope": scope}
        if client_secret is not None:
            payload["client_secret"] = client_secret
        raw = await self._post("/oauth/device/code", data=payload)
        return V2DeviceCode.model_validate(raw)

    async def authorize_device(
        self,
        device_code: str,
        client_id: str,
        client_secret: str | None = None,
    ) -> V2TokenResponse:
        """Authorize a device (poll)."""
        payload: dict[str, Any] = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": client_id,
            "device_code": device_code,
        }
        if client_secret is not None:
            payload["client_secret"] = client_secret
        raw = await self._post("/oauth/device/token", data=payload)
        return V2TokenResponse.model_validate(raw)

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------

    async def get_account_info(self) -> V2AccountInfo:
        """Return account profile and storage info from GET /user."""
        raw = await self._get("/user")
        return V2AccountInfo.model_validate(raw)

    async def get_settings(self) -> V2AccountSettings:
        """Return account settings from GET /me/settings."""
        raw = await self._get("/me/settings")
        return V2AccountSettings.model_validate(raw)

    async def get_memory_bandwidth(self) -> V2Quota:
        """Return storage and bandwidth quota from GET /me/quota."""
        raw = await self._get("/me/quota")
        return V2Quota.model_validate(raw)

    async def get_devices(self) -> list[Any]:
        """Return registered devices (not available in V2 API)."""
        return []

    # ------------------------------------------------------------------
    # Filesystem
    # ------------------------------------------------------------------

    async def list_contents(
        self,
        folder_id: int | str = 0,
        content_type: str = "folder",
    ) -> V2FolderContents:
        """List contents of a folder.

        Uses ``/fs/root/contents`` for folder_id 0 (root) and
        ``/fs/folder/{id}/contents`` for all other folders.
        """
        if str(folder_id) == "0":
            raw = await self._get("/fs/root/contents")
        else:
            raw = await self._get(f"/fs/folder/{folder_id}/contents")
        return V2FolderContents.model_validate(raw)

    async def get_folder(self, folder_id: int) -> V2FolderContents:
        """Get folder metadata (no file listing) from GET /fs/folder/{id}."""
        raw = await self._get(f"/fs/folder/{folder_id}")
        return V2FolderContents.model_validate(raw)

    async def get_file(self, file_id: int) -> V2FileInfo:
        """Get file metadata from GET /fs/file/{id}."""
        raw = await self._get(f"/fs/file/{file_id}")
        return V2FileInfo.model_validate(raw)

    async def create_folder(
        self, name: str, parent_id: int | None = None
    ) -> V2AddFolderResult:
        """Create a new folder via POST /fs/folder."""
        payload: dict[str, Any] = {"name": name}
        if parent_id is not None:
            payload["parent_id"] = parent_id
        raw = await self._post("/fs/folder", json_body=payload)
        return V2AddFolderResult.model_validate(raw if isinstance(raw, dict) else {})

    async def rename(
        self,
        new_name: str,
        *,
        folder_id: int | None = None,
        folder_file_id: int | None = None,
    ) -> dict[str, Any]:
        """Rename is not available in the V2 API."""
        raise NotImplementedError("rename is not supported by the V2 API.")

    async def delete(self, items: list[dict[str, Any]]) -> V2DeleteResult:
        """Delete items via POST /fs/batch/delete.

        Parameters
        ----------
        items:
            List of ``{"type": "folder"|"folder_file"|"torrent", "id": N}``.
        """
        raw = await self._post(
            "/fs/batch/delete",
            data={"delete_arr": json.dumps(items)},
        )
        return V2DeleteResult.model_validate(raw if isinstance(raw, dict) else {})

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    async def get_tasks(self) -> V2TasksResponse:
        """Return all tasks from GET /tasks."""
        raw = await self._get("/tasks")
        return V2TasksResponse.model_validate(raw)

    async def get_task(self, task_id: int) -> V2SingleTaskResponse:
        """Return a single task from GET /tasks/{id}."""
        raw = await self._get(f"/tasks/{task_id}")
        return V2SingleTaskResponse.model_validate(raw)

    async def add_task(
        self,
        *,
        torrent_magnet: str | None = None,
        wishlist_id: int | None = None,
        folder_id: int | None = None,
    ) -> V2AddTaskResult:
        """Add a new torrent task via POST /tasks.

        Returns
        -------
        V2AddTaskResult
            On success: ``{user_torrent_id, title, success, torrent_hash}``.
            On queue-full (no space): ``{reason_phrase, wt: {...}}``.
        """
        payload: dict[str, Any] = {}
        if torrent_magnet is not None:
            payload["torrent_magnet"] = torrent_magnet
        if wishlist_id is not None:
            payload["wishlist_id"] = wishlist_id
        if folder_id is not None:
            payload["folder_id"] = folder_id
        raw = await self._post("/tasks", json_body=payload)
        return V2AddTaskResult.model_validate(raw)

    async def delete_task(self, task_id: int) -> V2DeleteResult:
        """Delete a task via DELETE /tasks/{id}."""
        raw = await self._delete(f"/tasks/{task_id}")
        return V2DeleteResult.model_validate(raw if isinstance(raw, dict) else {})

    async def pause_task(self, task_id: int) -> dict[str, Any]:
        """Pause an active task via POST /tasks/{id}/pause."""
        raw = await self._post(f"/tasks/{task_id}/pause")
        return raw if isinstance(raw, dict) else {}

    async def resume_task(self, task_id: int) -> dict[str, Any]:
        """Resume a paused task via POST /tasks/{id}/resume."""
        raw = await self._post(f"/tasks/{task_id}/resume")
        return raw if isinstance(raw, dict) else {}

    # ------------------------------------------------------------------
    # Wishlist
    # ------------------------------------------------------------------

    async def get_wishlist(self) -> list[V2WishlistItem]:
        """Return wishlist items from GET /tasks/wishlist.

        Returns an empty list when the wishlist is empty (API returns 404).
        """
        try:
            raw = await self._get("/tasks/wishlist")
        except NotFoundError:
            return []
        items: list[Any] = raw if isinstance(raw, list) else raw.get("items", [])
        return [V2WishlistItem.model_validate(i) for i in items]

    async def delete_wishlist_item(self, wishlist_id: int) -> dict[str, Any]:
        """Delete a wishlist item."""
        raw = await self._delete(f"/tasks/wishlist/{wishlist_id}")
        return raw if isinstance(raw, dict) else {}

    # ------------------------------------------------------------------
    # Downloads
    # ------------------------------------------------------------------

    async def get_file_url(self, file_id: int) -> V2DownloadURL:
        """Return a download URL for a file from GET /download/file/{id}/url."""
        raw = await self._get(f"/download/file/{file_id}/url")
        return V2DownloadURL.model_validate(raw)

    async def init_archive(
        self,
        uuid: str,
        folder_id: int,
        items: list[dict[str, Any]],
    ) -> V2ArchiveInit:
        """Initialise a ZIP archive download via PUT /download/archive/init/{uuid}."""
        raw = await self._put(
            f"/download/archive/init/{uuid}",
            json_body={
                "folder_id": folder_id,
                "archive_arr": items,
            },
        )
        return V2ArchiveInit.model_validate(raw)

    async def get_file_bytes(self, file_id: int) -> bytes:
        """Download file content as bytes via GET /download/file/{id} (follows redirect)."""
        session = self._get_session()
        async with session.get(
            self._url(f"/download/file/{file_id}"),
            headers={**self._build_headers(), "Accept": "*/*"},
            allow_redirects=True,
        ) as resp:
            if resp.status >= 400:
                try:
                    body: dict[str, Any] = await resp.json(content_type=None)
                except Exception:
                    body = {}
                _check_v2_error(body, resp.status)
            return await resp.read()

    async def stream_file(
        self,
        file_id: int,
        *,
        chunk_size: int = 8192,
    ) -> AsyncGenerator[bytes, None]:
        """Stream file content as byte chunks via GET /download/file/{id}."""
        session = self._get_session()
        async with session.get(
            self._url(f"/download/file/{file_id}"),
            headers={**self._build_headers(), "Accept": "*/*"},
            allow_redirects=True,
        ) as resp:
            if resp.status >= 400:
                try:
                    body: dict[str, Any] = await resp.json(content_type=None)
                except Exception:
                    body = {}
                _check_v2_error(body, resp.status)
            async for chunk in resp.content.iter_chunked(chunk_size):
                if chunk:
                    yield chunk

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search_files(self, query: str) -> dict[str, Any]:
        """Search files and folders via GET /search/fs?q={query}."""
        raw = await self._get("/search/fs", params={"q": query})
        return raw if isinstance(raw, dict) else {}

    # ------------------------------------------------------------------
    # Presentations
    # ------------------------------------------------------------------

    async def get_folder_presentations(self, folder_id: int) -> V2FolderPresentations:
        """Get media presentations for a folder via GET /presentations/folder/{id}."""
        raw = await self._get(f"/presentations/folder/{folder_id}")
        return V2FolderPresentations.model_validate(raw)

    # ------------------------------------------------------------------
    # Subtitles
    # ------------------------------------------------------------------

    async def get_subtitles(self, file_id: int) -> V2SubtitlesList:
        """Get subtitles for a file via GET /subtitles/file/{id}."""
        raw = await self._get(f"/subtitles/file/{file_id}")
        return V2SubtitlesList.model_validate(raw)

    # ------------------------------------------------------------------
    # V1-only stubs
    # ------------------------------------------------------------------

    async def scan_page(self, url: str) -> dict[str, Any]:
        """Not available in the Seedr API."""
        raise NotImplementedError("scan_page is not supported by the Seedr API.")

    async def create_archive(
        self,
        items: list[dict[str, Any]],
        folder_id: int | None = None,
    ) -> dict[str, Any]:
        """Not available in the Seedr API."""
        raise NotImplementedError("create_archive is not supported by the Seedr API.")

    async def modify_account_name(self, first_name: str, last_name: str) -> dict[str, Any]:
        """Not available in the Seedr API."""
        raise NotImplementedError("modify_account_name is not supported by the Seedr API.")

    async def modify_account_password(
        self, current_password: str, new_password: str
    ) -> dict[str, Any]:
        """Not available in the Seedr API."""
        raise NotImplementedError("modify_account_password is not supported by the Seedr API.")

    async def get_torrent_progress(self, progress_url: str) -> dict[str, Any]:
        """Not supported in V2 — use the progress_url from torrent_payload directly."""
        raise NotImplementedError("get_torrent_progress is only supported via the V1 adapter.")
