"""AutoAdapter — routes requests to V1 or V2 depending on operation availability."""

from __future__ import annotations

from typing import Any

from seedr_api.adapters.v1 import V1Adapter
from seedr_api.adapters.v2 import V2Adapter


class AutoAdapter:
    """Adapter that prefers V2 for all operations but falls back to V1.

    When only a V1 token (access_token + optional refresh_token) is available,
    requests go to V1.  When a V2 OAuth token is available, V2 is preferred
    for all operations that support it.

    Parameters
    ----------
    v1:
        Optional pre-configured V1 adapter.
    v2:
        Optional pre-configured V2 adapter.
    prefer_v2:
        When both adapters are available, prefer V2. Defaults to True.
    """

    def __init__(
        self,
        *,
        v1: V1Adapter | None = None,
        v2: V2Adapter | None = None,
        prefer_v2: bool = True,
    ) -> None:
        if v1 is None and v2 is None:
            raise ValueError("At least one of v1 or v2 must be provided.")
        self._v1 = v1
        self._v2 = v2
        self._prefer_v2 = prefer_v2

    @property
    def v1(self) -> V1Adapter | None:
        return self._v1

    @property
    def v2(self) -> V2Adapter | None:
        return self._v2

    def _pick(self, v2_available: bool = True) -> V1Adapter | V2Adapter:
        """Return the preferred adapter for a given operation."""
        if self._v2 is not None and (self._prefer_v2 or self._v1 is None) and v2_available:
            return self._v2
        if self._v1 is not None:
            return self._v1
        assert self._v2 is not None
        return self._v2

    def update_token(self, access_token: str, api_version: str = "v2") -> None:
        """Update the access token on the appropriate adapter."""
        if api_version == "v1" and self._v1 is not None:
            self._v1.update_token(access_token)
        elif self._v2 is not None:
            self._v2.update_token(access_token)

    async def close(self) -> None:
        """Close all underlying sessions."""
        if self._v1 is not None:
            await self._v1.close()
        if self._v2 is not None:
            await self._v2.close()

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    async def login(self, username: str, password: str) -> Any:
        """Authenticate — always uses V1 (V2 requires CAPTCHA)."""
        if self._v1 is None:
            raise RuntimeError("V1 adapter required for login.")
        return await self._v1.login(username, password)

    async def refresh_token(self, refresh_token: str, client_id: str) -> Any:
        """Refresh token — prefer V2, fall back to V1."""
        return await self._pick().refresh_token(refresh_token, client_id)

    async def get_device_code(self, client_id: str) -> Any:
        """Request device code — prefer V2."""
        return await self._pick().get_device_code(client_id)

    async def authorize_device(self, device_code: str, client_id: str) -> Any:
        """Authorize device — prefer V2."""
        return await self._pick().authorize_device(device_code, client_id)

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------

    async def get_settings(self) -> Any:
        return await self._pick().get_settings()

    async def get_memory_bandwidth(self) -> Any:
        return await self._pick().get_memory_bandwidth()

    async def get_devices(self) -> Any:
        if self._v1 is not None:
            return await self._v1.get_devices()
        return []

    # ------------------------------------------------------------------
    # Filesystem
    # ------------------------------------------------------------------

    async def list_contents(
        self,
        folder_id: int | str = 0,
        content_type: str = "folder",
    ) -> Any:
        return await self._pick().list_contents(folder_id, content_type)

    async def get_folder(self, folder_id: int) -> Any:
        return await self._pick().get_folder(folder_id)

    async def get_file(self, file_id: int) -> Any:
        return await self._pick().get_file(file_id)

    async def create_folder(self, name: str, parent_id: int | None = None) -> Any:
        return await self._pick().create_folder(name, parent_id)

    async def rename(
        self,
        new_name: str,
        *,
        folder_id: int | None = None,
        folder_file_id: int | None = None,
    ) -> Any:
        return await self._pick().rename(
            new_name,
            folder_id=folder_id,
            folder_file_id=folder_file_id,
        )

    async def delete(self, items: list[dict[str, Any]]) -> Any:
        return await self._pick().delete(items)

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    async def get_tasks(self) -> Any:
        return await self._pick().get_tasks()

    async def get_task(self, task_id: int) -> Any:
        return await self._pick().get_task(task_id)

    async def add_task(
        self,
        *,
        torrent_magnet: str | None = None,
        wishlist_id: int | None = None,
        folder_id: int | None = None,
    ) -> Any:
        return await self._pick().add_task(
            torrent_magnet=torrent_magnet,
            wishlist_id=wishlist_id,
            folder_id=folder_id,
        )

    async def delete_task(self, task_id: int) -> Any:
        return await self._pick().delete_task(task_id)

    # ------------------------------------------------------------------
    # Downloads
    # ------------------------------------------------------------------

    async def get_file_url(self, file_id: int) -> Any:
        return await self._pick().get_file_url(file_id)

    async def get_file_bytes(self, file_id: int) -> bytes:
        # Prefer V2 for direct download
        if self._v2 is not None:
            return await self._v2.get_file_bytes(file_id)
        if self._v1 is not None:
            return await self._v1.get_file_bytes(file_id)
        raise RuntimeError("No adapter available.")

    async def init_archive(
        self,
        uuid: str,
        folder_id: int,
        items: list[dict[str, Any]],
    ) -> Any:
        # Archive init is V2-only
        if self._v2 is not None:
            return await self._v2.init_archive(uuid, folder_id, items)
        if self._v1 is not None:
            return await self._v1.init_archive(uuid, folder_id, items)
        raise RuntimeError("No adapter available.")

    # ------------------------------------------------------------------
    # Search / Page scan
    # ------------------------------------------------------------------

    async def search_files(self, query: str) -> Any:
        return await self._pick().search_files(query)

    async def scan_page(self, url: str) -> Any:
        """Not available in the Seedr API (returns unknown_func)."""
        raise NotImplementedError("scan_page is not supported by the Seedr API.")

    # ------------------------------------------------------------------
    # Presentations
    # ------------------------------------------------------------------

    async def get_folder_presentations(self, folder_id: int) -> Any:
        # Prefer V2 for presentations
        if self._v2 is not None:
            return await self._v2.get_folder_presentations(folder_id)
        assert self._v1 is not None
        return await self._v1.get_folder_presentations(folder_id)

    # ------------------------------------------------------------------
    # Subtitles
    # ------------------------------------------------------------------

    async def get_subtitles(self, file_id: int) -> Any:
        # Prefer V2 for subtitles
        if self._v2 is not None:
            return await self._v2.get_subtitles(file_id)
        assert self._v1 is not None
        return await self._v1.get_subtitles(file_id)

    # ------------------------------------------------------------------
    # Wishlist
    # ------------------------------------------------------------------

    async def get_wishlist(self) -> Any:
        return await self._pick().get_wishlist()

    async def delete_wishlist_item(self, wishlist_id: int) -> Any:
        return await self._pick().delete_wishlist_item(wishlist_id)

    # ------------------------------------------------------------------
    # Account modification — not available in the Seedr API
    # ------------------------------------------------------------------

    async def modify_account_name(self, first_name: str, last_name: str) -> Any:
        """Not available in the Seedr API (returns unknown_func)."""
        raise NotImplementedError("modify_account_name is not supported by the Seedr API.")

    async def modify_account_password(
        self, current_password: str, new_password: str
    ) -> Any:
        """Not available in the Seedr API (returns unknown_func)."""
        raise NotImplementedError("modify_account_password is not supported by the Seedr API.")

    # ------------------------------------------------------------------
    # Torrent progress (V1 only, via direct progress_url)
    # ------------------------------------------------------------------

    async def get_torrent_progress(self, progress_url: str) -> Any:
        """Fetch live torrent download progress (V1 only)."""
        if self._v1 is not None:
            return await self._v1.get_torrent_progress(progress_url)
        raise NotImplementedError("get_torrent_progress is only supported via the V1 adapter.")

    # ------------------------------------------------------------------
    # Archive creation — not available in V1 API
    # ------------------------------------------------------------------

    async def create_archive(
        self,
        items: list[dict[str, Any]],
        folder_id: int | None = None,
    ) -> Any:
        """Not available in the Seedr API (returns unknown_func)."""
        raise NotImplementedError("create_archive is not supported by the Seedr API.")
