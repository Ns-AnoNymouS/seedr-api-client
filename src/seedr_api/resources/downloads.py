"""Downloads resource — streaming files and retrieving download URLs."""

from __future__ import annotations

import uuid as uuid_module
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from seedr_api.resources._base import BaseResource


class DownloadsResource(BaseResource):
    """Provides methods for downloading files from Seedr."""

    async def get_download_url(self, file_id: int) -> str:
        """Retrieve a temporary direct download URL for a file.

        Parameters
        ----------
        file_id:
            The numeric file ID.

        Returns
        -------
        str
            A short-lived direct download URL.
        """
        result = await self._adapter.get_file_url(file_id)
        # Handle both V1FetchFileResult and V2DownloadURL
        if hasattr(result, "url") and result.url is not None:
            return result.url
        if isinstance(result, dict):
            return str(result.get("url", ""))
        return str(result)

    async def get_file_bytes(self, file_id: int) -> bytes:
        """Download an entire file into memory as bytes.

        .. warning::
            Avoid for large files; prefer :meth:`stream_file`.

        Parameters
        ----------
        file_id:
            The numeric file ID.

        Returns
        -------
        bytes
            Raw file content.
        """
        return await self._adapter.get_file_bytes(file_id)

    @asynccontextmanager
    async def stream_file(
        self,
        file_id: int,
        *,
        chunk_size: int = 8192,
    ) -> AsyncGenerator[AsyncGenerator[bytes, None], None]:
        """Stream a file as an async generator of byte chunks.

        Parameters
        ----------
        file_id:
            The numeric file ID.
        chunk_size:
            Bytes per chunk. Defaults to 8 KiB.

        Yields
        ------
        AsyncGenerator[bytes, None]
            An async iterable of byte chunks.

        Example
        -------
        ::

            async with client.downloads.stream_file(123) as stream:
                with open("movie.mkv", "wb") as f:
                    async for chunk in stream:
                        f.write(chunk)
        """
        from seedr_api.adapters.auto import AutoAdapter
        from seedr_api.adapters.v2 import V2Adapter

        adapter = self._adapter
        v2 = adapter.v2 if isinstance(adapter, AutoAdapter) else adapter
        if not isinstance(v2, V2Adapter):
            raise NotImplementedError(
                "File streaming is only supported with the V2 adapter."
            )
        yield v2.stream_file(file_id, chunk_size=chunk_size)

    async def init_archive(
        self,
        items: list[dict[str, Any]],
        *,
        folder_id: int = 0,
        archive_uuid: str | None = None,
    ) -> Any:
        """Initialise a ZIP archive download for a set of files/folders (V2 only).

        Parameters
        ----------
        items:
            List of item descriptors, e.g.
            ``[{"type": "folder_file", "id": 123}]``.
        folder_id:
            Parent folder ID for the archive.
        archive_uuid:
            Client-generated UUID. Auto-generated if not provided.

        Returns
        -------
        V2ArchiveInit
            Archive initialisation response including download URL.
        """
        archive_id = archive_uuid or str(uuid_module.uuid4())
        return await self._adapter.init_archive(archive_id, folder_id, items)

