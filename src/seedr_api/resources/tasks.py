"""Tasks resource — managing torrent download tasks and wishlist."""

from __future__ import annotations

from typing import Any

from seedr_api.resources._base import BaseResource


class TasksResource(BaseResource):
    """Provides methods to manage torrent download tasks in Seedr."""

    async def list(self) -> Any:
        """Return all active torrent tasks.

        Returns
        -------
        V2TasksResponse or list
            All current tasks.
        """
        return await self._adapter.get_tasks()

    async def get(self, task_id: int) -> Any:
        """Return a single task by ID (V2 only).

        Parameters
        ----------
        task_id:
            The numeric task ID.

        Returns
        -------
        V2SingleTaskResponse
        """
        return await self._adapter.get_task(task_id)

    async def add_magnet(
        self,
        magnet: str,
        *,
        folder_id: int | None = None,
    ) -> Any:
        """Add a new task from a magnet link.

        Parameters
        ----------
        magnet:
            The magnet URI (``magnet:?xt=...``).
        folder_id:
            Destination folder ID. Defaults to root.

        Returns
        -------
        Task result.

        Raises
        ------
        InsufficientSpaceError
            If there is not enough space; the torrent is auto-added to
            the wishlist and accessible via ``exc.wishlist_item``.
        """
        return await self._adapter.add_task(
            torrent_magnet=magnet,
            folder_id=folder_id,
        )

    async def add_from_wishlist(
        self,
        wishlist_id: int,
        *,
        folder_id: int | None = None,
    ) -> Any:
        """Add a task from a wishlist entry.

        Parameters
        ----------
        wishlist_id:
            The numeric wishlist item ID.
        folder_id:
            Destination folder ID. Defaults to root.

        Returns
        -------
        Task result.
        """
        return await self._adapter.add_task(
            wishlist_id=wishlist_id,
            folder_id=folder_id,
        )

    async def delete(self, task_id: int) -> Any:
        """Delete a task by ID.

        Uses DELETE /tasks/{id} on V2 and the V1 torrent-delete endpoint on V1.

        Parameters
        ----------
        task_id:
            The numeric task/torrent ID.
        """
        return await self._adapter.delete_task(task_id)

    async def delete_torrent(self, torrent_id: int) -> Any:
        """Delete a torrent task (alias for :meth:`delete`).

        Parameters
        ----------
        torrent_id:
            The numeric torrent task ID.
        """
        return await self._adapter.delete_task(torrent_id)

    async def get_torrent_progress(self, progress_url: str) -> Any:
        """Fetch live download progress for an active torrent (V1 only).

        Parameters
        ----------
        progress_url:
            The ``progress_url`` field from a torrent entry returned by
            :meth:`list` (e.g. ``tasks[0].progress_url``).

        Returns
        -------
        V1TorrentProgress
            Download progress including percentage, speed, and ETA.

        Raises
        ------
        NotImplementedError
            When using a V2-only adapter.
        """
        return await self._adapter.get_torrent_progress(progress_url)
