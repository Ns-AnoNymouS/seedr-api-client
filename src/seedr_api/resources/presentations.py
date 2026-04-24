"""Presentations resource — media streaming URLs and playlists."""

from __future__ import annotations

from typing import Any

from seedr_api.models.media import PresentationURL
from seedr_api.resources._base import BaseResource


class PresentationsResource(BaseResource):
    """Provides methods to retrieve media presentation URLs for files and folders.

    Presentation types include: ``thumbnail``, ``video``, ``audio``,
    ``preview``, ``video-playlist``, etc.
    """

    async def get_file_presentation(
        self,
        file_id: int,
        presentation_type: str,
    ) -> PresentationURL:
        """Get a media presentation URL for a specific file.

        Parameters
        ----------
        file_id:
            The numeric file ID.
        presentation_type:
            The presentation type string (e.g. ``"thumbnail"``, ``"video"``).

        Returns
        -------
        PresentationURL
            URL and metadata for the presentation.
        """
        data: Any = await self._http.get(
            f"/presentations/file/{file_id}/{presentation_type}"
        )
        return PresentationURL.model_validate(
            {"url": data.get("url", ""), "presentation_type": presentation_type, **data}
        )

    async def get_folder_presentations(self, folder_id: int) -> list[PresentationURL]:
        """Get all available presentation URLs for a folder.

        Parameters
        ----------
        folder_id:
            The numeric folder ID.

        Returns
        -------
        list[PresentationURL]
            Available presentations for the folder.
        """
        data: Any = await self._http.get(f"/presentations/folder/{folder_id}")
        items: list[Any] = (
            data if isinstance(data, list) else data.get("presentations", [data])
        )
        return [PresentationURL.model_validate(item) for item in items]

    async def get_folder_presentation(
        self,
        folder_id: int,
        presentation_type: str,
    ) -> PresentationURL:
        """Get a specific presentation type for a folder.

        Parameters
        ----------
        folder_id:
            The numeric folder ID.
        presentation_type:
            The presentation type (e.g. ``"video-playlist"``).

        Returns
        -------
        PresentationURL
            URL and metadata for the folder presentation.
        """
        data: Any = await self._http.get(
            f"/presentations/folder/{folder_id}/{presentation_type}"
        )
        return PresentationURL.model_validate(
            {"url": data.get("url", ""), "presentation_type": presentation_type, **data}
        )
