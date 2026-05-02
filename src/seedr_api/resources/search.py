"""Search resource — searching files and folders."""

from __future__ import annotations

from typing import Any

from seedr_api.resources._base import BaseResource


class SearchResource(BaseResource):
    """Provides search methods for finding files and folders."""

    async def search(self, query: str) -> Any:
        """Search files and folders within the authenticated user's Seedr account.

        Parameters
        ----------
        query:
            Search string to match against file and folder names.

        Returns
        -------
        V1SearchResult or dict
            Matching files and folders.
        """
        return await self._adapter.search_files(query)
