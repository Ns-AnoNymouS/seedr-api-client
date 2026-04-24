"""Tests for SearchResource and PresentationsResource."""

import re

from aioresponses import aioresponses

from seedr_api.client import SeedrClient

OAUTH_BASE = "https://www.seedr.cc/api/v0.1"


# ---------------------------------------------------------------------------
# SearchResource
# ---------------------------------------------------------------------------


async def test_search_returns_results(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        re.compile(r".*/search/fs"),
        payload={"results": [{"id": 1, "name": "movie.mkv", "size": 1000}]},
    )
    async with token_client:
        items = await token_client.search.search("movie")
    assert len(items) == 1
    assert items[0].name == "movie.mkv"


async def test_search_empty(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(re.compile(r".*/search/fs"), payload=[])
    async with token_client:
        items = await token_client.search.search("nothing")
    assert items == []


async def test_search_folder_item(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        re.compile(r".*/search/fs"),
        payload={
            "results": [{"id": 5, "name": "TV Shows", "size": 0, "type": "folder"}]
        },
    )
    async with token_client:
        items = await token_client.search.search("TV")
    from seedr_api.models.filesystem import FolderInfo

    assert isinstance(items[0], FolderInfo)


async def test_scrape_torrents(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{OAUTH_BASE}/scrape/html/torrents",
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
        f"{OAUTH_BASE}/presentations/file/10/thumbnail",
        payload={"url": "https://cdn.seedr.cc/thumb/10"},
    )
    async with token_client:
        p = await token_client.presentations.get_file_presentation(10, "thumbnail")
    assert p.url == "https://cdn.seedr.cc/thumb/10"
    assert p.presentation_type == "thumbnail"


async def test_get_folder_presentations(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{OAUTH_BASE}/presentations/folder/2",
        payload=[{"url": "https://cdn.seedr.cc/playlist/2"}],
    )
    async with token_client:
        items = await token_client.presentations.get_folder_presentations(2)
    assert len(items) == 1
    assert "playlist" in items[0].url


async def test_get_folder_presentation(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{OAUTH_BASE}/presentations/folder/2/video-playlist",
        payload={"url": "https://cdn.seedr.cc/vp/2"},
    )
    async with token_client:
        p = await token_client.presentations.get_folder_presentation(
            2, "video-playlist"
        )
    assert p.url == "https://cdn.seedr.cc/vp/2"
    assert p.presentation_type == "video-playlist"
