"""Tests for SearchResource and PresentationsResource."""

from __future__ import annotations

import re

from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from tests.conftest import API_BASE

# ---------------------------------------------------------------------------
# SearchResource
# ---------------------------------------------------------------------------


async def test_search_returns_file_results(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        re.compile(r".*/search/fs"),
        payload={
            "folders": [],
            "files": [{"id": 1, "name": "movie.mkv", "size": 1000, "hash": "abc"}],
        },
    )
    async with token_client:
        result = await token_client.search.search("movie")
    # V2 adapter returns raw dict
    assert isinstance(result, dict)
    assert len(result.get("files", [])) == 1
    assert result["files"][0]["name"] == "movie.mkv"


async def test_search_empty(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        re.compile(r".*/search/fs"),
        payload={"folders": [], "files": [], "torrents": []},
    )
    async with token_client:
        result = await token_client.search.search("nothing")
    assert result.get("files") == []
    assert result.get("folders") == []


async def test_search_with_folders(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        re.compile(r".*/search/fs"),
        payload={
            "folders": [
                {"id": 5, "path": "TV Shows", "size": 0, "last_update": "2024-01-01"}
            ],
            "files": [],
        },
    )
    async with token_client:
        result = await token_client.search.search("TV")
    assert len(result.get("folders", [])) == 1
    assert result["folders"][0]["path"] == "TV Shows"


# ---------------------------------------------------------------------------
# PresentationsResource
# ---------------------------------------------------------------------------


async def test_get_folder_presentations(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/presentations/folder/2",
        payload={
            "folder": {"id": 2, "name": "Movies", "path": "/Movies"},
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
        payload={"folder": {"id": 99, "name": "Empty"}, "files": [], "total_files": 0},
    )
    async with token_client:
        fp = await token_client.presentations.get_folder_presentations(99)
    assert fp.total_files == 0
    assert fp.files == []
