"""V2 subtitles models — lenient, all Optional."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class V2SubtitleInfo(BaseModel):
    """A subtitle track entry."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    title: str | None = None
    url: str | None = None
    language: str | None = None
    language_name: str | None = None
    source: str | None = None


class V2SubtitlesList(BaseModel):
    """Response from GET /subtitles/file/{id}.

    Real API shape:
    {subtitles:[], file_subtitles:[{id,title,url}], folder_file_subtitles:[]}
    """

    model_config = ConfigDict(extra="ignore")

    subtitles: list[V2SubtitleInfo] = Field(default_factory=list)
    file_subtitles: list[V2SubtitleInfo] = Field(default_factory=list)
    folder_file_subtitles: list[V2SubtitleInfo] = Field(default_factory=list)
