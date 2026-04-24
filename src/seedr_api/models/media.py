"""Pydantic v2 models for Seedr API responses — media/presentations domain."""

from __future__ import annotations

from pydantic import BaseModel


class PresentationURL(BaseModel):
    """A media presentation URL (stream, thumbnail, playlist, etc.)."""

    url: str
    presentation_type: str | None = None
    content_type: str | None = None


class SubtitleInfo(BaseModel):
    """Metadata for a subtitle track associated with a file."""

    id: int | None = None
    language: str | None = None
    language_name: str | None = None
    source: str | None = None
    url: str | None = None


class SubtitleSearchResult(BaseModel):
    """A subtitle search result from OpenSubtitles."""

    id: str | None = None
    language: str | None = None
    language_name: str | None = None
    movie_name: str | None = None
    upload_date: str | None = None
    download_count: int | None = None
    url: str | None = None
