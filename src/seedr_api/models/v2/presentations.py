"""V2 presentations models — lenient, all Optional."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _V2VideoInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    duration: float | None = None
    progress: float | None = None
    os_hash: str | None = None


class V2FilePresentations(BaseModel):
    """A single file's presentations inside a folder presentations response."""

    model_config = ConfigDict(extra="ignore")

    file_id: int | None = None
    name: str | None = None
    size: int | None = None
    hash: str | None = None
    is_audio: bool | None = None
    is_video: bool | None = None
    is_image: bool | None = None
    is_document: bool | None = None
    presentations: dict[str, Any] | None = None
    thumbnail: str | None = None
    video_info: _V2VideoInfo | None = None


class _V2FolderMeta(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    name: str | None = None
    path: str | None = None


class V2FolderPresentations(BaseModel):
    """Response from GET /presentations/folder/{id}."""

    model_config = ConfigDict(extra="ignore")

    folder: _V2FolderMeta | None = None
    files: list[V2FilePresentations] = Field(default_factory=list)
    total_files: int | None = None
