"""Tests for SearchResource and PresentationsResource."""

import re

from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from seedr_api.models.filesystem import FolderInfo
from tests.conftest import API_BASE

# ---------------------------------------------------------------------------
# SearchResource
# ---------------------------------------------------------------------------


async def test_search_returns_file_results(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        re.compile(r".*/search/fs"),
        payload={"folders": [], "files": [{"id": 1, "name": "movie.mkv", "size": 1000}]},
    )
    async with token_client:
        items = await token_client.search.search("movie")
    assert len(items) == 1
    assert items[0].name == "movie.mkv"  # type: ignore[union-attr]


async def test_search_empty(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        re.compile(r".*/search/fs"),
        payload={"folders": [], "files": [], "torrents": []},
    )
    async with token_client:
        items = await token_client.search.search("nothing")
    assert items == []


async def test_search_folder_item(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        re.compile(r".*/search/fs"),
        payload={"folders": [{"id": 5, "path": "TV Shows", "size": 0}], "files": []},
    )
    async with token_client:
        items = await token_client.search.search("TV")
    assert isinstance(items[0], FolderInfo)


async def test_scrape_torrents(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/scrape/html/torrents",
        payload={"results": ["magnet:?xt=urn:btih:abc123"]},
    )
    async with token_client:
        links = await token_client.search.scrape_torrents("https://example.com/page")
    assert len(links) == 1
    assert links[0].startswith("magnet:")


# ---------------------------------------------------------------------------
# PresentationsResource
# ---------------------------------------------------------------------------


async def test_get_file_presentation(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/presentations/file/10/thumbnail",
        payload={"48": "https://cdn.seedr.cc/thumb/48.jpg", "220": "https://cdn.seedr.cc/thumb/220.jpg"},
    )
    async with token_client:
        urls = await token_client.presentations.get_file_presentation(10, "thumbnail")
    assert "48" in urls
    assert urls["48"].startswith("https://")


async def test_get_folder_presentations(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/presentations/folder/2",
        payload={
            "files": [
                {
                    "file_id": 10,
                    "name": "movie.mkv",
                    "is_video": True,
                    "presentations": {"video": {"hls": "https://cdn.seedr.cc/v.m3u8"}},
                    "thumbnail": "https://cdn.seedr.cc/thumb.jpg",
                }
            ],
            "total_files": 1,
        },
    )
    async with token_client:
        fp = await token_client.presentations.get_folder_presentations(2)
    assert fp.total_files == 1
    assert fp.files[0].file_id == 10
    assert fp.files[0].is_video is True


async def test_get_folder_presentations_empty(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/presentations/folder/99",
        payload={"files": [], "total_files": 0},
    )
    async with token_client:
        fp = await token_client.presentations.get_folder_presentations(99)
    assert fp.total_files == 0
    assert fp.files == []
