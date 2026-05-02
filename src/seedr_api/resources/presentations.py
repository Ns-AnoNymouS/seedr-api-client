"""Presentations resource — media streaming URLs and playlists."""

from __future__ import annotations

from typing import Any

from seedr_api.resources._base import BaseResource


class PresentationsResource(BaseResource):
    """Provides methods to retrieve media presentation URLs for files and folders."""

    async def get_folder_presentations(self, folder_id: int) -> Any:
        """Get all media presentation URLs for files inside a folder.

        Parameters
        ----------
        folder_id:
            The numeric folder ID.

        Returns
        -------
        V2FolderPresentations
            Presentation data for every file in the folder.
        """
        return await self._adapter.get_folder_presentations(folder_id)
