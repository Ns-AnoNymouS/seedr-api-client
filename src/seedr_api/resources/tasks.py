"""Tasks resource — managing torrent download tasks."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import aiohttp

from seedr_api.models.tasks import Task
from seedr_api.resources._base import BaseResource


class TasksResource(BaseResource):
    """Provides methods to manage torrent download tasks in Seedr."""

    async def list(self) -> list[Task]:
        """Return all active torrent tasks.

        Returns
        -------
        list[Task]
            All current tasks.
        """
        data: Any = await self._http.get("/tasks")
        tasks: list[Any] = data if isinstance(data, list) else data.get("tasks", [])
        return [Task.model_validate(t) for t in tasks]

    async def get(self, task_id: int) -> Task:
        """Return details for a single task.

        Parameters
        ----------
        task_id:
            The numeric task ID.

        Returns
        -------
        Task
            Task details and progress.
        """
        data: Any = await self._http.get(f"/tasks/{task_id}")
        return Task.model_validate(data)

    async def add_magnet(self, magnet: str, folder_id: int | None = None) -> Task:
        """Add a new task from a magnet link.

        Parameters
        ----------
        magnet:
            The magnet URI (``magnet:?xt=...``).
        folder_id:
            Destination folder ID. Defaults to root.

        Returns
        -------
        Task
            The created task.
        """
        payload: dict[str, Any] = {"magnet": magnet}
        if folder_id is not None:
            payload["folder_id"] = folder_id
        data: Any = await self._http.post("/tasks", data=payload)
        return Task.model_validate(data)

    async def add_url(self, url: str, folder_id: int | None = None) -> Task:
        """Add a new task from a direct URL to a torrent.

        Parameters
        ----------
        url:
            Direct download URL pointing to a torrent file.
        folder_id:
            Destination folder ID. Defaults to root.

        Returns
        -------
        Task
            The created task.
        """
        payload: dict[str, Any] = {"url": url}
        if folder_id is not None:
            payload["folder_id"] = folder_id
        data: Any = await self._http.post("/tasks", data=payload)
        return Task.model_validate(data)

    async def add_torrent_file(
        self,
        file_path: str | Path,
        folder_id: int | None = None,
    ) -> Task:
        """Add a new task by uploading a local ``.torrent`` file.

        Parameters
        ----------
        file_path:
            Local filesystem path to the ``.torrent`` file.
        folder_id:
            Destination folder ID. Defaults to root.

        Returns
        -------
        Task
            The created task.
        """
        path = Path(file_path)
        file_bytes = await asyncio.to_thread(path.read_bytes)
        form = aiohttp.FormData()
        form.add_field(
            "file",
            file_bytes,
            filename=path.name,
            content_type="application/x-bittorrent",
        )
        if folder_id is not None:
            form.add_field("folder_id", str(folder_id))
        data: Any = await self._http.post("/tasks", form_data=form)
        return Task.model_validate(data)

    async def pause(self, task_id: int) -> None:
        """Pause an active task.

        Parameters
        ----------
        task_id:
            The numeric task ID.
        """
        await self._http.post(f"/tasks/{task_id}/pause")

    async def resume(self, task_id: int) -> None:
        """Resume a paused task.

        Parameters
        ----------
        task_id:
            The numeric task ID.
        """
        await self._http.post(f"/tasks/{task_id}/resume")

    async def delete(self, task_id: int) -> None:
        """Delete a task (does **not** delete downloaded files).

        Parameters
        ----------
        task_id:
            The numeric task ID.
        """
        await self._http.delete(f"/tasks/{task_id}")
