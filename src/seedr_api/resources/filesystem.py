"""Filesystem resource — folders, files, and batch operations."""

from __future__ import annotations

from typing import Any

from seedr_api.models.filesystem import (
    BatchResult,
    FileInfo,
    FolderContents,
    FolderInfo,
)
from seedr_api.resources._base import BaseResource


class FilesystemResource(BaseResource):
    """Provides methods for browsing and managing files and folders in Seedr."""

    # ------------------------------------------------------------------
    # Root folder
    # ------------------------------------------------------------------

    async def get_root(self) -> FolderInfo:
        """Return metadata for the root folder.

        Returns
        -------
        FolderInfo
            Root folder details.
        """
        data: Any = await self._http.get("/fs/root")
        return FolderInfo.model_validate(data)

    async def list_root_contents(self) -> FolderContents:
        """List all contents (subfolders, files, active torrents) of the root folder.

        Returns
        -------
        FolderContents
            Root folder contents.
        """
        data: Any = await self._http.get("/fs/root/contents")
        return FolderContents.model_validate(data)

    # ------------------------------------------------------------------
    # Folder operations
    # ------------------------------------------------------------------

    async def get_folder(self, folder_id: int) -> FolderInfo:
        """Return metadata for a specific folder.

        Parameters
        ----------
        folder_id:
            The numeric ID of the folder.

        Returns
        -------
        FolderInfo
            Folder metadata.
        """
        data: Any = await self._http.get(f"/fs/folder/{folder_id}")
        return FolderInfo.model_validate(data)

    async def list_folder_contents(self, folder_id: int) -> FolderContents:
        """List all contents of a specific folder.

        Parameters
        ----------
        folder_id:
            The numeric ID of the folder.

        Returns
        -------
        FolderContents
            Folder contents.
        """
        data: Any = await self._http.get(f"/fs/folder/{folder_id}/contents")
        return FolderContents.model_validate(data)

    async def create_folder(
        self, name: str, parent_id: int | None = None
    ) -> FolderInfo:
        """Create a new folder.

        Parameters
        ----------
        name:
            Name of the new folder.
        parent_id:
            Parent folder ID. Defaults to the root folder.

        Returns
        -------
        FolderInfo
            Created folder metadata.
        """
        payload: dict[str, Any] = {"name": name}
        if parent_id is not None:
            payload["parent_id"] = parent_id
        data: Any = await self._http.post("/fs/folder", data=payload)
        return FolderInfo.model_validate(data)

    async def delete_folder(self, folder_id: int) -> None:
        """Delete a folder and all its contents.

        Parameters
        ----------
        folder_id:
            The numeric ID of the folder to delete.
        """
        await self._http.delete(f"/fs/folder/{folder_id}")

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    async def get_file(self, file_id: int) -> FileInfo:
        """Return metadata for a specific file.

        Parameters
        ----------
        file_id:
            The numeric ID of the file.

        Returns
        -------
        FileInfo
            File metadata.
        """
        data: Any = await self._http.get(f"/fs/file/{file_id}")
        return FileInfo.model_validate(data)

    async def delete_file(self, file_id: int) -> None:
        """Delete a specific file.

        Parameters
        ----------
        file_id:
            The numeric ID of the file to delete.
        """
        await self._http.delete(f"/fs/file/{file_id}")

    # ------------------------------------------------------------------
    # Path lookup
    # ------------------------------------------------------------------

    async def get_by_path(self, path: str) -> FolderInfo | FileInfo:
        """Retrieve a file or folder by its absolute path within Seedr.

        Parameters
        ----------
        path:
            Absolute path (e.g. ``"/My Folder/file.mkv"``).

        Returns
        -------
        FolderInfo | FileInfo
            The located resource.
        """
        data: Any = await self._http.get("/fs/path", params={"path": path})
        if data.get("files") is not None or data.get("folders") is not None:
            return FolderInfo.model_validate(data)
        return FileInfo.model_validate(data)

    # ------------------------------------------------------------------
    # Batch operations
    # ------------------------------------------------------------------

    async def batch_copy(
        self,
        item_ids: list[int],
        destination_folder_id: int,
    ) -> BatchResult:
        """Copy multiple files/folders to a destination folder.

        Parameters
        ----------
        item_ids:
            List of file or folder IDs to copy.
        destination_folder_id:
            Target folder ID.

        Returns
        -------
        BatchResult
            Success status and any errors.
        """
        data: Any = await self._http.post(
            "/fs/batch/copy",
            data={"ids": item_ids, "destination": destination_folder_id},
        )
        return BatchResult.model_validate(data)

    async def batch_move(
        self,
        item_ids: list[int],
        destination_folder_id: int,
    ) -> BatchResult:
        """Move multiple files/folders to a destination folder.

        Parameters
        ----------
        item_ids:
            List of file or folder IDs to move.
        destination_folder_id:
            Target folder ID.

        Returns
        -------
        BatchResult
            Success status and any errors.
        """
        data: Any = await self._http.post(
            "/fs/batch/move",
            data={"ids": item_ids, "destination": destination_folder_id},
        )
        return BatchResult.model_validate(data)

    async def batch_delete(self, item_ids: list[int]) -> BatchResult:
        """Delete multiple files, folders, or torrent tasks.

        Parameters
        ----------
        item_ids:
            List of file/folder/task IDs to delete.

        Returns
        -------
        BatchResult
            Success status and any errors.
        """
        data: Any = await self._http.post(
            "/fs/batch/delete",
            data={"ids": item_ids},
        )
        return BatchResult.model_validate(data)
