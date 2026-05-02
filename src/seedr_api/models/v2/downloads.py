"""V2 downloads models — lenient, all Optional."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class V2DownloadURL(BaseModel):
    """Response from GET /download/file/{id}/url."""

    model_config = ConfigDict(extra="ignore")

    url: str | None = None
    name: str | None = None
    success: bool | None = None


class V2ArchiveInit(BaseModel):
    """Response from PUT /download/archive/init/{uuid}."""

    model_config = ConfigDict(extra="ignore")

    success: bool | None = None
    uniq: str | None = None
    url: str | None = None
