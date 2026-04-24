"""Presentations resource — media streaming URLs and playlists."""

from __future__ import annotations

from typing import Any

from seedr_api.models.media import FilePresentations, FolderPresentations
from seedr_api.resources._base import BaseResource


class PresentationsResource(BaseResource):
    """Provides methods to retrieve media presentation URLs for files and folders."""

    async def get_file_presentation(
        self,
        file_id: int,
        presentation_type: str,
    ) -> dict[str, str]:
        """Get presentation URLs for a specific file and type.

        Required scope: ``media.read``

        For ``"thumbnail"``, returns a dict mapping sizes to URLs
        (e.g. ``{"48": "https://...", "220": "https://...", ...}``).

        Parameters
        ----------
        file_id:
            The numeric file ID.
        presentation_type:
            Presentation type string (e.g. ``"thumbnail"``).

        Returns
        -------
        dict[str, str]
            Mapping of size/variant to URL.
        """
        data: Any = await self._http.get(
            f"/presentations/file/{file_id}/{presentation_type}"
        )
        return {k: str(v) for k, v in data.items() if isinstance(v, str)}

    async def get_folder_presentations(
        self, folder_id: int
    ) -> FolderPresentations:
        """Get all media presentation URLs for files inside a folder.

        Required scope: ``media.read``

        Parameters
        ----------
        folder_id:
            The numeric folder ID.

        Returns
        -------
        FolderPresentations
            Presentation data for every file in the folder.
        """
        data: Any = await self._http.get(f"/presentations/folder/{folder_id}")
        return FolderPresentations.model_validate(data)

    async def get_folder_presentation(
        self,
        folder_id: int,
        presentation_type: str,
    ) -> dict[str, str]:
        """Get a specific presentation type for a folder.

        Required scope: ``media.read``

        Parameters
        ----------
        folder_id:
            The numeric folder ID.
        presentation_type:
            Presentation type (e.g. ``"video-playlist"``).

        Returns
        -------
        dict[str, str]
            Mapping of size/variant to URL.
        """
        data: Any = await self._http.get(
            f"/presentations/folder/{folder_id}/{presentation_type}"
        )
        return {k: str(v) for k, v in data.items() if isinstance(v, str)}
