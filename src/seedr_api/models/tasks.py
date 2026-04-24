"""Pydantic v2 models for Seedr API responses — tasks (torrents) domain."""

from __future__ import annotations

from pydantic import BaseModel


class Task(BaseModel):
    """Represents a torrent download task in Seedr."""

    id: int
    name: str
    progress: float | None = None
    size: int | None = None
    folder_created: int | None = None
    status: str | None = None
    created_time: str | None = None
