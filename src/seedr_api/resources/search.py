"""Search and Scrape resource."""

from __future__ import annotations

from typing import Any

from seedr_api.models.filesystem import FileInfo, FolderInfo
from seedr_api.resources._base import BaseResource


class SearchResource(BaseResource):
    """Provides search and web-scraping methods."""

    async def search(self, query: str) -> list[FileInfo | FolderInfo]:
        """Search files and folders within the authenticated user's Seedr account.

        Required scope: ``files.read``

        Parameters
        ----------
        query:
            Search string to match against file and folder names.

        Returns
        -------
        list[FileInfo | FolderInfo]
            Matching files and folders (folders first, then files).
        """
        data: Any = await self._http.get("/search/fs", params={"q": query})
        if isinstance(data, list):
            return []
        items: list[FileInfo | FolderInfo] = []
        for folder in data.get("folders", []):
            items.append(FolderInfo.model_validate(folder))
        for file_ in data.get("files", []):
            items.append(FileInfo.model_validate(file_))
        return items

    async def scrape_torrents(self, url: str) -> list[str]:
        """Scrape a webpage for torrent files or magnet links.

        Required scope: ``files.read``

        Parameters
        ----------
        url:
            The URL of the webpage to scrape.

        Returns
        -------
        list[str]
            A list of discovered magnet links or torrent file URLs.
        """
        data: Any = await self._http.post(
            "/scrape/html/torrents",
            data={"url": url},
        )
        results: list[Any] = data if isinstance(data, list) else data.get("results", [])
        return [str(r) for r in results]
