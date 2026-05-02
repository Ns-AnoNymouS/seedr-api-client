"""V2 filesystem models — lenient, all Optional."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class V2PresentationURLs(BaseModel):
    """Presentation URLs nested inside file metadata."""

    model_config = ConfigDict(extra="ignore")

    image: dict[str, str] | None = None
    video: dict[str, str] | None = None


class V2FileInfo(BaseModel):
    """A file entry from V2 GET /fs/file/{id} or folder contents."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    name: str | None = None
    size: int | None = None
    hash: str | None = None
    folder_id: int | None = None
    folder_path: str | None = None
    last_update: str | None = None
    is_audio: bool | None = None
    is_video: bool | None = None
    is_image: bool | None = None
    is_document: bool | None = None
    presentation_urls: V2PresentationURLs | None = None
    video_progress: str | None = None
    is_available: bool | None = None
    thumb: str | None = None


class V2FolderItem(BaseModel):
    """A subfolder entry inside V2 folder contents.

    The API returns {id, path, size, last_update}. The folder name is in ``path``.
    """

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    path: str | None = None
    size: int | None = None
    last_update: str | None = None

    @property
    def name(self) -> str | None:
        return self.path


class V2FolderContents(BaseModel):
    """Response from GET /fs/root/contents or GET /fs/folder/{id}/contents.

    When called as GET /fs/folder/{id} (no /contents), only the metadata
    fields are populated (id, path, size, parent, etc.) and folders/files
    default to empty lists.
    """

    model_config = ConfigDict(extra="ignore")

    space_max: int | None = None
    space_used: int | None = None
    space_scope: str | None = None
    saw_walkthrough: int | None = None
    id: int | None = None
    timestamp: str | None = None
    path: str | None = None
    size: int | None = None
    parent: int | None = None
    folders: list[V2FolderItem] = Field(default_factory=list)
    files: list[V2FileInfo] = Field(default_factory=list)
    torrents: list[Any] = Field(default_factory=list)
    tasks: list[Any] = Field(default_factory=list)
    album_groups: list[Any] = Field(default_factory=list)


class V2AddFolderResult(BaseModel):
    """Response from POST /fs/folder (create folder).

    Note: ``id`` is returned as a string by the API; Pydantic coerces to int.
    """

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    path: str | None = None
    success: bool | None = None

    @property
    def name(self) -> str | None:
        return self.path


class V2DeleteResult(BaseModel):
    """Response from POST /fs/batch/delete or DELETE /tasks/{id}."""

    model_config = ConfigDict(extra="ignore")

    success: bool | None = None
