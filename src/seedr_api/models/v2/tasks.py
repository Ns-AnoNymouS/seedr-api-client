"""V2 tasks models — lenient, all Optional."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class V2Task(BaseModel):
    """A torrent task entry from V2 GET /tasks or GET /tasks/{id}."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    user_id: int | None = None
    type: str | None = None
    operation: str | None = None
    provider: str | None = None
    name: str | None = None
    state: str | None = None
    progress: float | None = None
    size: int | None = None
    storage_size: int | None = None
    folder_id: int | None = None
    folder_created_id: int | None = None
    items_total: int | None = None
    items_completed: int | None = None
    error: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None
    node_id: str | None = None
    last_update: str | None = None
    torrent_payload: dict[str, Any] | None = None

    @property
    def title(self) -> str | None:
        return self.name

    @property
    def torrent_hash(self) -> str | None:
        if self.torrent_payload:
            return self.torrent_payload.get("hash")
        return None


class V2TasksResponse(BaseModel):
    """Response from GET /tasks."""

    model_config = ConfigDict(extra="ignore")

    tasks: list[V2Task] = Field(default_factory=list)
    user_id: int | None = None


class V2SingleTaskResponse(BaseModel):
    """Response from GET /tasks/{id}."""

    model_config = ConfigDict(extra="ignore")

    task: V2Task | None = None
    success: bool | None = None


class V2WishlistTask(BaseModel):
    """Wishlist entry returned inside queue-full (add-to-wishlist) responses."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    user_id: int | None = None
    title: str | None = None
    size: int | None = None
    torrent_hash: str | None = None
    torrent_magnet: str | None = None
    torrent_meta: str | None = None
    is_private: int | None = None
    created: str | None = None
    added: int | None = None


class V2AddTaskResult(BaseModel):
    """Response from POST /tasks.

    Success: {user_torrent_id, title, success, torrent_hash}
    Queue-full: {reason_phrase, wt: {id, user_id, title, ...}}
    """

    model_config = ConfigDict(extra="ignore")

    user_torrent_id: int | None = None
    title: str | None = None
    success: bool | None = None
    torrent_hash: str | None = None
    reason_phrase: str | None = None
    wt: dict[str, Any] | None = None

    @property
    def id(self) -> int | None:
        return self.user_torrent_id

    @property
    def name(self) -> str | None:
        return self.title

    @property
    def state(self) -> str | None:
        if self.wt:
            return "wishlist"
        if self.success:
            return "added"
        return None

    @property
    def progress(self) -> float | None:
        return None
