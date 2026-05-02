"""V1 API models — strict, required fields match real API responses."""

from __future__ import annotations

from seedr_api.models.v1.account import (
    V1AccountSettings,
    V1Device,
    V1MemoryBandwidth,
    V1WishlistItem,
)
from seedr_api.models.v1.auth import V1DeviceCode, V1RefreshToken, V1TokenResponse
from seedr_api.models.v1.filesystem import (
    V1FileItem,
    V1FolderContents,
    V1FolderItem,
    V1TorrentItem,
)
from seedr_api.models.v1.tasks import (
    V1AddFolderResult,
    V1DeleteResult,
    V1FetchFileResult,
    V1RenameResult,
    V1SearchResult,
)

__all__ = [
    "V1AccountSettings",
    "V1AddFolderResult",
    "V1DeleteResult",
    "V1Device",
    "V1DeviceCode",
    "V1FetchFileResult",
    "V1FileItem",
    "V1FolderContents",
    "V1FolderItem",
    "V1MemoryBandwidth",
    "V1RefreshToken",
    "V1RenameResult",
    "V1SearchResult",
    "V1TokenResponse",
    "V1TorrentItem",
    "V1WishlistItem",
]
