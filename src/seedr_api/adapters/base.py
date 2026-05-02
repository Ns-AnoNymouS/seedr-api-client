"""SeedrAdapter Protocol / ABC — defines the interface all adapters must implement."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SeedrAdapter(Protocol):
    """Protocol defining the common adapter interface.

    All adapters (V1, V2, Auto) must implement these methods.
    Resources call the adapter methods; the adapter handles transport,
    URL construction, error normalisation, and model parsing.
    """

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    async def login(self, username: str, password: str) -> Any:
        """Authenticate with username/password and return a token object."""
        ...

    async def refresh_token(self, refresh_token: str, client_id: str) -> Any:
        """Refresh an access token and return a new token object."""
        ...

    async def get_device_code(self, client_id: str) -> Any:
        """Request a device code and return a device code object."""
        ...

    async def authorize_device(self, device_code: str, client_id: str) -> Any:
        """Authorize a device and return a token object."""
        ...

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------

    async def get_settings(self) -> Any:
        """Return account settings."""
        ...

    async def get_memory_bandwidth(self) -> Any:
        """Return memory and bandwidth quota."""
        ...

    async def get_devices(self) -> Any:
        """Return registered devices."""
        ...

    # ------------------------------------------------------------------
    # Filesystem
    # ------------------------------------------------------------------

    async def list_contents(self, folder_id: int | str) -> Any:
        """List folder contents."""
        ...

    async def get_folder(self, folder_id: int) -> Any:
        """Get folder metadata."""
        ...

    async def get_file(self, file_id: int) -> Any:
        """Get file metadata."""
        ...

    async def create_folder(self, name: str, parent_id: int | None) -> Any:
        """Create a new folder."""
        ...

    async def rename(
        self,
        new_name: str,
        *,
        folder_id: int | None = None,
        folder_file_id: int | None = None,
    ) -> Any:
        """Rename a folder or file."""
        ...

    async def delete(self, items: list[dict[str, Any]]) -> Any:
        """Delete items (folders, files, torrents)."""
        ...

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    async def get_tasks(self) -> Any:
        """Return all active tasks."""
        ...

    async def get_task(self, task_id: int) -> Any:
        """Return a single task by ID."""
        ...

    async def add_task(
        self,
        *,
        torrent_magnet: str | None = None,
        wishlist_id: int | None = None,
        folder_id: int | None = None,
    ) -> Any:
        """Add a new task."""
        ...

    async def delete_task(self, task_id: int) -> Any:
        """Delete a task by ID."""
        ...

    # ------------------------------------------------------------------
    # Downloads
    # ------------------------------------------------------------------

    async def get_file_url(self, file_id: int) -> Any:
        """Return a download URL for a file."""
        ...

    async def get_file_bytes(self, file_id: int) -> bytes:
        """Download a file as bytes (V2 only; V1 raises NotImplementedError)."""
        ...

    async def init_archive(
        self, uuid: str, folder_id: int, items: list[dict[str, Any]]
    ) -> Any:
        """Initialise a ZIP archive download."""
        ...

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search_files(self, query: str) -> Any:
        """Search files and folders."""
        ...

    # ------------------------------------------------------------------
    # Presentations
    # ------------------------------------------------------------------

    async def get_folder_presentations(self, folder_id: int) -> Any:
        """Get media presentations for a folder."""
        ...

    # ------------------------------------------------------------------
    # Subtitles
    # ------------------------------------------------------------------

    async def get_subtitles(self, file_id: int) -> Any:
        """Get subtitles for a file."""
        ...

    # ------------------------------------------------------------------
    # Wishlist
    # ------------------------------------------------------------------

    async def get_wishlist(self) -> Any:
        """Return the wishlist."""
        ...

    async def delete_wishlist_item(self, wishlist_id: int) -> Any:
        """Delete a wishlist item."""
        ...

    # ------------------------------------------------------------------
    # V1-specific (stubs raise NotImplementedError on V2)
    # ------------------------------------------------------------------

    async def scan_page(self, url: str) -> Any:
        """Not available in the Seedr API."""
        ...

    async def create_archive(
        self,
        items: list[dict[str, Any]],
        folder_id: int | None = None,
    ) -> Any:
        """Not available in the Seedr API."""
        ...

    async def modify_account_name(self, first_name: str, last_name: str) -> Any:
        """Update display name (V1 only)."""
        ...

    async def modify_account_password(
        self, current_password: str, new_password: str
    ) -> Any:
        """Change account password (V1 only)."""
        ...

    async def get_torrent_progress(self, progress_url: str) -> Any:
        """Fetch live torrent download progress (V1 only)."""
        ...

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the adapter and release resources."""
        ...
