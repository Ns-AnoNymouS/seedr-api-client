"""V2 API models — lenient, all Optional fields."""

from __future__ import annotations

from seedr_api.models.v2.account import (
    V2AccountInfo,
    V2AccountSettings,
    V2Quota,
    V2WishlistItem,
)
from seedr_api.models.v2.auth import V2DeviceCode, V2TokenResponse
from seedr_api.models.v2.downloads import V2ArchiveInit, V2DownloadURL
from seedr_api.models.v2.filesystem import (
    V2FileInfo,
    V2FolderContents,
    V2FolderItem,
    V2PresentationURLs,
)
from seedr_api.models.v2.presentations import V2FilePresentations, V2FolderPresentations
from seedr_api.models.v2.subtitles import V2SubtitleInfo, V2SubtitlesList
from seedr_api.models.v2.tasks import (
    V2AddTaskResult,
    V2Task,
    V2TasksResponse,
    V2WishlistTask,
)

__all__ = [
    "V2AccountInfo",
    "V2AccountSettings",
    "V2AddTaskResult",
    "V2ArchiveInit",
    "V2DeviceCode",
    "V2DownloadURL",
    "V2FileInfo",
    "V2FilePresentations",
    "V2FolderContents",
    "V2FolderItem",
    "V2FolderPresentations",
    "V2PresentationURLs",
    "V2Quota",
    "V2SubtitleInfo",
    "V2SubtitlesList",
    "V2Task",
    "V2TasksResponse",
    "V2TokenResponse",
    "V2WishlistItem",
    "V2WishlistTask",
]
