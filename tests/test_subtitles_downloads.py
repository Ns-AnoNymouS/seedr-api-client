"""Tests for SubtitlesResource and DownloadsResource."""

from __future__ import annotations

from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from tests.conftest import API_BASE

# ---------------------------------------------------------------------------
# SubtitlesResource
# ---------------------------------------------------------------------------


async def test_list_subtitles(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/subtitles/file/10",
        payload={
            "subtitles": [],
            "file_subtitles": [{"id": 1, "title": "English", "url": "https://sub.srt"}],
            "folder_file_subtitles": [],
        },
    )
    async with token_client:
        subs = await token_client.subtitles.list_subtitles(10)
    # Returns V2SubtitlesList
    assert len(subs.file_subtitles) == 1
    assert subs.file_subtitles[0].title == "English"


async def test_list_subtitles_empty(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/subtitles/file/10",
        payload={"subtitles": [], "file_subtitles": [], "folder_file_subtitles": []},
    )
    async with token_client:
        subs = await token_client.subtitles.list_subtitles(10)
    assert subs.file_subtitles == []
    assert subs.subtitles == []


# ---------------------------------------------------------------------------
# DownloadsResource
# ---------------------------------------------------------------------------


async def test_get_download_url(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/download/file/10/url",
        payload={"url": "https://cdn.seedr.cc/dl/token/file.mkv", "name": "file.mkv", "success": True},
    )
    async with token_client:
        url = await token_client.downloads.get_download_url(10)
    assert "seedr.cc" in url


async def test_get_file_bytes(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/download/file/10",
        body=b"binary data here",
    )
    async with token_client:
        data = await token_client.downloads.get_file_bytes(10)
    assert data == b"binary data here"


async def test_init_archive(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.put(
        re.compile(r".*/download/archive/init/.*"),
        payload={"success": True, "uniq": "abc123", "url": "https://cdn.seedr.cc/archive.zip"},
    )
    async with token_client:
        result = await token_client.downloads.init_archive(
            [{"type": "folder_file", "id": 10}],
            folder_id=0,
        )
    assert result.success is True
    assert result.uniq == "abc123"


# Need to import re for the URL pattern in test_init_archive
import re  # noqa: E402
