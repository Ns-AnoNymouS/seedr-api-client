"""Search and Scrape resource."""

from __future__ import annotations

from typing import Any

from seedr_api.models.filesystem import FileInfo, FolderInfo
from seedr_api.resources._base import BaseResource


class SearchResource(BaseResource):
    """Provides search and web-scraping methods."""

    async def search(self, query: str) -> list[FileInfo | FolderInfo]:
        """Search files and folders within the authenticated user's Seedr account.

        Parameters
        ----------
        query:
            Search string to match against file and folder names.

        Returns
        -------
        list[FileInfo | FolderInfo]
            Matching files and folders.
        """
        data: Any = await self._http.get("/search/fs", params={"q": query})
        results: list[Any] = data if isinstance(data, list) else data.get("results", [])
        items: list[FileInfo | FolderInfo] = []
        for item in results:
            if "files" in item or item.get("type") == "folder":
                items.append(FolderInfo.model_validate(item))
            else:
                items.append(FileInfo.model_validate(item))
        return items

    async def scrape_torrents(self, url: str) -> list[str]:
        """Scrape a webpage for torrent files or magnet links.

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
