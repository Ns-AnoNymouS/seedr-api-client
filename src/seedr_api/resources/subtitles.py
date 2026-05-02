"""Subtitles resource — listing subtitles for files."""

from __future__ import annotations

from typing import Any

from seedr_api.resources._base import BaseResource


class SubtitlesResource(BaseResource):
    """Provides methods for managing subtitles associated with files in Seedr."""

    async def list_subtitles(self, file_id: int) -> Any:
        """List all available subtitles for a file.

        Parameters
        ----------
        file_id:
            The numeric file ID.

        Returns
        -------
        V2SubtitlesList
            Available subtitle tracks (subtitles, file_subtitles,
            folder_file_subtitles).
        """
        return await self._adapter.get_subtitles(file_id)
