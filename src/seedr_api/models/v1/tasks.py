"""V1 task/operation result models — strict Pydantic v2 models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class V1AddFolderResult(BaseModel):
    """Response from resource.php?func=add_folder.

    Real API shape: {success:true, id:"str_number", path:str, result:true}
    """

    model_config = ConfigDict(extra="ignore")

    success: bool
    id: str
    path: str
    result: bool


class V1AddTorrentResult(BaseModel):
    """Response from resource.php?func=add_torrent.

    Real API shape: {user_torrent_id:int, result:true, ...}
    """

    model_config = ConfigDict(extra="ignore")

    user_torrent_id: int
    result: bool


class V1RenameResult(BaseModel):
    """Response from resource.php?func=rename.

    Real API shape: {success:true, result:true}
    """

    model_config = ConfigDict(extra="ignore")

    success: bool
    result: bool


class V1DeleteResult(BaseModel):
    """Response from resource.php?func=delete.

    Real API shape: {success:true, result:true}
    """

    model_config = ConfigDict(extra="ignore")

    success: bool
    result: bool


class V1FetchFileResult(BaseModel):
    """Response from resource.php?func=fetch_file.

    Real API shape: {url:str, name:str, success:true, result:true}
    """

    model_config = ConfigDict(extra="ignore")

    url: str
    name: str
    success: bool
    result: bool


class _V1SearchFileItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    size: int
    hash: str
    folder_id: int
    last_update: str
    presentation_urls: dict[str, Any] | None = None
    thumb: str | None = None


class _V1SearchFolderItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    path: str
    size: int
    last_update: str
    name: str
    fullname: str


class V1DeleteWishlistResult(BaseModel):
    """Response from resource.php?func=delete_wishlist.

    Real API shape: {success:true, result:true}
    """

    model_config = ConfigDict(extra="ignore")

    success: bool
    result: bool


class V1SearchResult(BaseModel):
    """Response from resource.php?func=search_files.

    Real API shape:
    {max_space, used_space, space_scope, path, name,
     torrents:[], folders:[...], files:[...], result:true}
    """

    model_config = ConfigDict(extra="ignore")

    max_space: int
    used_space: int
    space_scope: str
    path: str
    name: str
    torrents: list[Any] = Field(default_factory=list)
    folders: list[_V1SearchFolderItem] = Field(default_factory=list)
    files: list[_V1SearchFileItem] = Field(default_factory=list)
    result: bool


class V1TorrentProgress(BaseModel):
    """Response from GET torrent.progress_url — live download progress.

    Fields are all optional because the shape varies with torrent state.
    """

    model_config = ConfigDict(extra="ignore")

    progress: int | None = None
    speed_down: str | None = None
    speed_up: str | None = None
    eta: str | None = None
    queue: int | None = None
    result: bool | None = None
