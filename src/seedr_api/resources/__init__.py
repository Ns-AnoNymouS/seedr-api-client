"""Resources package — all API resource classes."""

from __future__ import annotations

from seedr_api.resources.account import AccountResource
from seedr_api.resources.auth import AuthResource
from seedr_api.resources.downloads import DownloadsResource
from seedr_api.resources.filesystem import FilesystemResource
from seedr_api.resources.presentations import PresentationsResource
from seedr_api.resources.search import SearchResource
from seedr_api.resources.subtitles import SubtitlesResource
from seedr_api.resources.tasks import TasksResource

__all__ = [
    "AccountResource",
    "AuthResource",
    "DownloadsResource",
    "FilesystemResource",
    "PresentationsResource",
    "SearchResource",
    "SubtitlesResource",
    "TasksResource",
]
