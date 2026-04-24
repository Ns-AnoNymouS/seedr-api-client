"""Pydantic v2 models for Seedr API responses — media/presentations domain."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FilePresentations(BaseModel):
    """Media presentation data for a single file within a folder."""

    file_id: int | None = None
    name: str | None = None
    size: int | None = None
    hash: str | None = None
    is_video: bool = False
    is_audio: bool = False
    is_image: bool = False
    is_document: bool = False
    presentations: dict[str, Any] = Field(default_factory=dict)
    thumbnail: str | None = None
    video_info: dict[str, Any] | None = None


class FolderPresentations(BaseModel):
    """All media presentations for files inside a folder."""

    files: list[FilePresentations] = Field(default_factory=list)
    total_files: int = 0

    @model_validator(mode="after")
    def _derive_total_files(self) -> "FolderPresentations":
        if self.total_files == 0 and self.files:
            self.total_files = len(self.files)
        return self


class SubtitleInfo(BaseModel):
    """Metadata for a subtitle track associated with a file."""

    id: int | None = None
    language: str | None = None
    language_name: str | None = None
    source: str | None = None
    url: str | None = None


class SubtitleSearchResult(BaseModel):
    """A subtitle search result from the OpenSubtitles v2 API.

    Field names use the PascalCase aliases returned by the API
    (e.g. ``SubFileName``, ``SubLanguageID``) but are exposed under
    friendlier snake_case names on the Python object.
    """

    model_config = ConfigDict(populate_by_name=True)

    file_id: int | None = None
    filename: str | None = Field(None, alias="SubFileName")
    language_id: str | None = Field(None, alias="SubLanguageID")
    movie_name: str | None = Field(None, alias="MovieName")
    movie_year: int | None = Field(None, alias="MovieYear")
    download_count: int | None = Field(None, alias="SubDownloadsCnt")
    rating: float | None = Field(None, alias="SubRating")
    format: str | None = Field(None, alias="SubFormat")
    from_trusted: bool | None = None
    ai_translated: bool | None = None
    machine_translated: bool | None = None
    uploader: str | None = None
    release: str | None = None
