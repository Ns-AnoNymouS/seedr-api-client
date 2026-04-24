"""Pydantic v2 models for Seedr API responses — tasks (torrents) domain."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Task(BaseModel):
    """Represents a torrent download task in Seedr."""

    model_config = ConfigDict(populate_by_name=True)

    # Seedr returns user_torrent_id / title in the add-magnet response
    id: int = Field(alias="user_torrent_id")
    name: str = Field(alias="title")
    success: bool | None = None
    torrent_hash: str | None = None
    state: str | None = None
    progress: float | None = None
    size: int | None = None
    storage_size: int | None = None
    folder_id: int | None = None
    folder_created_id: int | None = None
    user_id: int | None = None
    type: str | None = None
    operation: str | None = None
    items_total: int | None = None
    items_completed: int | None = None
    created_at: str | None = None
    started_at: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None
    last_update: str | None = None
    error: str | None = None
    node_id: str | None = None
    torrent_payload: dict[str, Any] | None = None
