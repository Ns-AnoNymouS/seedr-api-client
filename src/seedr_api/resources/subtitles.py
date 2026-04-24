"""Subtitles resource — listing, uploading, and searching subtitles."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import aiohttp

from seedr_api.models.media import SubtitleInfo, SubtitleSearchResult
from seedr_api.resources._base import BaseResource


class SubtitlesResource(BaseResource):
    """Provides methods for managing subtitles associated with files in Seedr."""

    async def list_subtitles(self, file_id: int) -> list[SubtitleInfo]:
        """List all available subtitles for a file.

        Parameters
        ----------
        file_id:
            The numeric file ID.

        Returns
        -------
        list[SubtitleInfo]
            Available subtitle tracks.
        """
        data: Any = await self._http.get(f"/subtitles/file/{file_id}")
        subtitles: list[Any] = (
            data if isinstance(data, list) else data.get("subtitles", [])
        )
        return [SubtitleInfo.model_validate(s) for s in subtitles]

    async def upload(self, file_id: int, subtitle_path: str | Path) -> SubtitleInfo:
        """Upload a subtitle file and associate it with a Seedr file.

        Parameters
        ----------
        file_id:
            The numeric file ID to associate the subtitle with.
        subtitle_path:
            Local path to the subtitle file (``.srt``, ``.vtt``, etc.).

        Returns
        -------
        SubtitleInfo
            Metadata for the uploaded subtitle.
        """
        path = Path(subtitle_path)
        file_bytes = await asyncio.to_thread(path.read_bytes)
        form = aiohttp.FormData()
        form.add_field(
            "file",
            file_bytes,
            filename=path.name,
            content_type="text/plain",
        )
        data: Any = await self._http.post(f"/subtitles/file/{file_id}", form_data=form)
        return SubtitleInfo.model_validate(data)

    async def search_opensubtitles(
        self,
        *,
        query: str | None = None,
        imdb_id: str | None = None,
        language: str | None = None,
    ) -> list[SubtitleSearchResult]:
        """Search for subtitles on OpenSubtitles.

        Parameters
        ----------
        query:
            Text search query (movie/show title).
        imdb_id:
            IMDB ID for exact title matching.
        language:
            ISO 639-1 language code (e.g. ``"en"``, ``"fr"``).

        Returns
        -------
        list[SubtitleSearchResult]
            Matching subtitle results.
        """
        payload: dict[str, Any] = {}
        if query is not None:
            payload["query"] = query
        if imdb_id is not None:
            payload["imdb_id"] = imdb_id
        if language is not None:
            payload["language"] = language
        data: Any = await self._http.post("/subtitles/v2/search", data=payload)
        results: list[Any] = (
            data if isinstance(data, list) else data.get("subtitles", [])
        )
        return [SubtitleSearchResult.model_validate(r) for r in results]

    async def link_opensubtitles(
        self,
        file_id: int,
        subtitle_id: str,
    ) -> SubtitleInfo:
        """Link an OpenSubtitles subtitle to a file in your Seedr library.

        Parameters
        ----------
        file_id:
            The numeric Seedr file ID.
        subtitle_id:
            The OpenSubtitles subtitle ID from :meth:`search_opensubtitles`.

        Returns
        -------
        SubtitleInfo
            Metadata for the linked subtitle.
        """
        data: Any = await self._http.post(
            f"/subtitles/file/{file_id}/opensubtitles-v2",
            data={"subtitle_id": subtitle_id},
        )
        return SubtitleInfo.model_validate(data)
