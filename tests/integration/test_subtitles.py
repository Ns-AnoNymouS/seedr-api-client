"""Integration tests — SubtitlesResource."""

from __future__ import annotations

import pytest

from seedr_api.client import SeedrClient
from seedr_api.models.media import SubtitleInfo, SubtitleSearchResult


async def _first_file_id(client: SeedrClient) -> int | None:
    contents = await client.filesystem.list_root_contents()
    for folder in contents.folders:
        inner = await client.filesystem.list_folder_contents(folder.id)
        if inner.files:
            return inner.files[0].id
    return None


async def test_list_subtitles(client: SeedrClient) -> None:
    file_id = await _first_file_id(client)
    if file_id is None:
        pytest.skip("No files available")
    subs = await client.subtitles.list_subtitles(file_id)
    assert isinstance(subs, list)
    for sub in subs:
        assert isinstance(sub, SubtitleInfo)


async def test_search_opensubtitles_by_query(client: SeedrClient) -> None:
    results = await client.subtitles.search_opensubtitles(query="inception", language="en")
    assert isinstance(results, list)
    assert len(results) > 0
    for r in results:
        assert isinstance(r, SubtitleSearchResult)
        assert isinstance(r.file_id, int)
        assert isinstance(r.filename, str)
        assert isinstance(r.language_id, str)
        assert isinstance(r.movie_name, str)


async def test_search_opensubtitles_by_imdb(client: SeedrClient) -> None:
    # tt1375666 = Inception; API expects numeric ID (no "tt" prefix)
    results = await client.subtitles.search_opensubtitles(imdb_id="tt1375666")
    assert isinstance(results, list)
    assert len(results) > 0
    for r in results:
        assert isinstance(r, SubtitleSearchResult)
        assert r.file_id is not None
