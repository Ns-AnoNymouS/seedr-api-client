"""Downloads resource — streaming files and resolving download URLs."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from seedr_api.resources._base import BaseResource


class DownloadsResource(BaseResource):
    """Provides methods for downloading files from Seedr."""

    @asynccontextmanager
    async def stream_file(
        self,
        file_id: int,
        *,
        chunk_size: int = 8192,
    ) -> AsyncGenerator[AsyncGenerator[bytes, None], None]:
        """Stream a file as an async generator of byte chunks.

        This context manager keeps the connection open while you consume
        the data, making it memory-efficient for large files.

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
        yield self._http.stream(
            f"/download/file/{file_id}",
            chunk_size=chunk_size,
        )

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
        return await self._http.get_bytes(f"/download/file/{file_id}")

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
        data: Any = await self._http.get(f"/download/file/{file_id}/url")
        url: str = data.get("url", data) if isinstance(data, dict) else str(data)
        return url

    async def get_archive_bytes(self, uniq: str) -> bytes:
        """Download a ZIP archive by its unique identifier.

        Parameters
        ----------
        uniq:
            The unique archive identifier provided by Seedr.

        Returns
        -------
        bytes
            Raw ZIP archive content.
        """
        return await self._http.get_bytes(f"/download/archive/{uniq}")
