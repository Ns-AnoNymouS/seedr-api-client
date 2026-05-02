"""Filesystem resource — folders, files, and batch operations."""

from __future__ import annotations

from typing import Any

from seedr_api.resources._base import BaseResource


class FilesystemResource(BaseResource):
    """Provides methods for browsing and managing files and folders."""

    # ------------------------------------------------------------------
    # Root folder
    # ------------------------------------------------------------------

    async def list_root_contents(self) -> Any:
        """List all contents of the root folder (folder_id=0).

        Returns
        -------
        V1FolderContents or V2FolderContents
            Root folder contents including subfolders, files, and torrents.
        """
        return await self._adapter.list_contents(0)

    # ------------------------------------------------------------------
    # Folder operations
    # ------------------------------------------------------------------

    async def get_folder(self, folder_id: int) -> Any:
        """Return metadata for a specific folder.

        Parameters
        ----------
        folder_id:
            The numeric ID of the folder.

        Returns
        -------
        Folder metadata.
        """
        return await self._adapter.get_folder(folder_id)

    async def list_folder_contents(self, folder_id: int) -> Any:
        """List all contents of a specific folder.

        Parameters
        ----------
        folder_id:
            The numeric ID of the folder.

        Returns
        -------
        Folder contents.
        """
        return await self._adapter.list_contents(folder_id)

    async def create_folder(self, name: str, parent_id: int | None = None) -> Any:
        """Create a new folder.

        Parameters
        ----------
        name:
            Name of the new folder.
        parent_id:
            Parent folder ID. Defaults to root (V2 only; V1 ignores parent_id).

        Returns
        -------
        Created folder result.
        """
        return await self._adapter.create_folder(name, parent_id)

    async def rename_folder(self, folder_id: int, new_name: str) -> Any:
        """Rename is not supported by the Seedr V2 API.

        This method delegates to the adapter's ``rename`` which raises
        ``NotImplementedError`` on V2.  It works on V1 adapters.
        """
        return await self._adapter.rename(new_name, folder_id=folder_id)

    async def rename_file(self, file_id: int, new_name: str) -> Any:
        """Rename is not supported by the Seedr V2 API.

        This method delegates to the adapter's ``rename`` which raises
        ``NotImplementedError`` on V2.  It works on V1 adapters.
        """
        return await self._adapter.rename(new_name, folder_file_id=file_id)

    async def delete_folder(self, folder_id: int) -> Any:
        """Delete a folder and all its contents.

        Parameters
        ----------
        folder_id:
            The numeric ID of the folder to delete.
        """
        return await self._adapter.delete([{"type": "folder", "id": folder_id}])

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    async def get_file(self, file_id: int) -> Any:
        """Return metadata for a specific file.

        Parameters
        ----------
        file_id:
            The numeric ID of the file.

        Returns
        -------
        File metadata.
        """
        return await self._adapter.get_file(file_id)

    async def delete_file(self, file_id: int) -> Any:
        """Delete a specific file.

        Parameters
        ----------
        file_id:
            The numeric ID of the file to delete.
        """
        return await self._adapter.delete([{"type": "folder_file", "id": file_id}])

    # ------------------------------------------------------------------
    # Batch operations
    # ------------------------------------------------------------------

    async def batch_delete(self, items: list[dict[str, Any]]) -> Any:
        """Delete multiple files, folders, or torrents.

        Parameters
        ----------
        items:
            List of dicts with ``type`` and ``id`` fields, e.g.
            ``[{"type": "folder", "id": 123}, {"type": "folder_file", "id": 456}]``.

        Returns
        -------
        Delete result.
        """
        return await self._adapter.delete(items)
