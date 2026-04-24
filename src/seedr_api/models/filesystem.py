"""Pydantic v2 models for Seedr API responses — filesystem domain."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """Metadata for a single file stored in Seedr."""

    id: int
    name: str
    size: int
    hash: str | None = None
    play_video: bool | None = None
    play_audio: bool | None = None
    created_time: str | None = None


class FolderInfo(BaseModel):
    """Metadata for a folder stored in Seedr."""

    id: int
    name: str
    size: int | None = None
    created_time: str | None = None


class TorrentTaskInfo(BaseModel):
    """Represents an active torrent task visible inside a folder."""

    id: int
    name: str
    progress: float | None = None
    size: int | None = None


class FolderContents(BaseModel):
    """Contents of a Seedr folder (subfolders, files, active torrents)."""

    id: int | None = None
    name: str | None = None
    size: int | None = None
    folders: list[FolderInfo] = Field(default_factory=list)
    files: list[FileInfo] = Field(default_factory=list)
    torrents: list[TorrentTaskInfo] = Field(default_factory=list)


class BatchResult(BaseModel):
    """Result of a batch copy, move, or delete operation."""

    success: bool
    errors: list[str] = Field(default_factory=list)
