"""V1 filesystem models — strict Pydantic v2 models matching real API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _V1PresentationURLs(BaseModel):
    model_config = ConfigDict(extra="ignore")

    image: dict[str, str] | None = None
    video: dict[str, str] | None = None


class V1FileItem(BaseModel):
    """A file entry within a V1 list_contents response."""

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    size: int
    hash: str
    folder_id: int
    last_update: str
    is_audio: bool
    is_video: bool
    presentation_urls: _V1PresentationURLs | None = None
    thumb: str | None = None
    folder_file_id: int
    play_video: bool
    play_audio: bool
    stream_video: bool
    stream_audio: bool


class V1FolderItem(BaseModel):
    """A subfolder entry within a V1 list_contents response."""

    model_config = ConfigDict(extra="ignore")

    id: int
    path: str
    size: int
    last_update: str
    name: str
    fullname: str


class V1TorrentItem(BaseModel):
    """An active torrent entry within a V1 list_contents response."""

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str | None = None
    progress: float | None = None
    size: int | None = None


class V1FolderContents(BaseModel):
    """Response from resource.php?func=list_contents.

    Real API shape:
    {space_max, space_used, space_scope, saw_walkthrough, id, timestamp,
     path, size, parent, folders:[...], files:[...], torrents:[], tasks:[],
     album_groups:[], result:true}
    """

    model_config = ConfigDict(extra="ignore")

    space_max: int
    space_used: int
    space_scope: str
    saw_walkthrough: int
    id: int
    timestamp: str
    path: str
    size: int
    parent: int
    folders: list[V1FolderItem] = Field(default_factory=list)
    files: list[V1FileItem] = Field(default_factory=list)
    torrents: list[V1TorrentItem] = Field(default_factory=list)
    tasks: list[Any] = Field(default_factory=list)
    album_groups: list[Any] = Field(default_factory=list)
    result: bool
