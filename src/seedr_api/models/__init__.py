"""Models package — re-exports all public model classes."""

from __future__ import annotations

from seedr_api.models.auth import DeviceCode, OAuthApp, TokenResponse
from seedr_api.models.filesystem import (
    BatchResult,
    FileInfo,
    FolderContents,
    FolderInfo,
    TorrentTaskInfo,
)
from seedr_api.models.media import PresentationURL, SubtitleInfo, SubtitleSearchResult
from seedr_api.models.tasks import Task
from seedr_api.models.user import Quota, UserInfo, UserSettings

__all__ = [
    "BatchResult",
    "DeviceCode",
    "FileInfo",
    "FolderContents",
    "FolderInfo",
    "OAuthApp",
    "PresentationURL",
    "Quota",
    "SubtitleInfo",
    "SubtitleSearchResult",
    "Task",
    "TokenResponse",
    "TorrentTaskInfo",
    "UserInfo",
    "UserSettings",
]
