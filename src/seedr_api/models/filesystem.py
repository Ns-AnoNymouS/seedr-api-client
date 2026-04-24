"""Pydantic v2 models for Seedr API responses — filesystem domain."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """Metadata for a single file stored in Seedr."""

    id: int
    name: str
    size: int
    hash: str | None = None
    folder_id: int | None = None
    folder_path: str | None = None
    last_update: str | None = None
    is_video: bool | None = None
    is_audio: bool | None = None
    is_image: bool | None = None
    is_document: bool | None = None
    thumb: str | None = None
    presentation_urls: dict[str, Any] | None = None
    video_progress: str | None = None
    is_available: bool | None = None


class FolderInfo(BaseModel):
    """Metadata for a folder stored in Seedr.

    The API returns the folder name in the ``path`` field.
    """

    id: int
    path: str | None = None
    size: int | None = None
    parent: int | None = None
    last_update: str | None = None
    timestamp: str | None = None


class TorrentTaskInfo(BaseModel):
    """Represents an active torrent task visible inside a folder."""

    id: int
    name: str
    progress: float | None = None
    size: int | None = None


class FolderContents(BaseModel):
    """Contents of a Seedr folder (subfolders, files, active torrents)."""

    id: int | None = None
    path: str | None = None
    size: int | None = None
    parent: int | None = None
    folders: list[FolderInfo] = Field(default_factory=list)
    files: list[FileInfo] = Field(default_factory=list)
    torrents: list[TorrentTaskInfo] = Field(default_factory=list)
    tasks: list[Any] = Field(default_factory=list)


class BatchResult(BaseModel):
    """Result of a batch copy, move, or delete operation."""

    success: bool
    errors: list[str] = Field(default_factory=list)
