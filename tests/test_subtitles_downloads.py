"""Tests for SubtitlesResource and DownloadsResource."""

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
        payload={"subtitles": [{"id": 1, "language": "en", "language_name": "English"}]},
    )
    async with token_client:
        subs = await token_client.subtitles.list_subtitles(10)
    assert len(subs) == 1
    assert subs[0].language == "en"


async def test_list_subtitles_list_response(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/subtitles/file/10",
        payload=[{"id": 2, "language": "fr"}],
    )
    async with token_client:
        subs = await token_client.subtitles.list_subtitles(10)
    assert subs[0].language == "fr"


async def test_search_opensubtitles(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/subtitles/v2/search",
        payload={"by_query": [{"SubFileName": "Inception.srt", "SubLanguageID": "en", "MovieName": "Inception"}], "by_hash": [], "total_count": 1},
    )
    async with token_client:
        results = await token_client.subtitles.search_opensubtitles(query="Inception")
    assert len(results) == 1
    assert results[0].movie_name == "Inception"


async def test_link_opensubtitles(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/subtitles/file/10/opensubtitles-v2",
        payload={"id": 99, "language": "en"},
    )
    async with token_client:
        sub = await token_client.subtitles.link_opensubtitles(10, "sub-123")
    assert sub.language == "en"


# ---------------------------------------------------------------------------
# DownloadsResource
# ---------------------------------------------------------------------------


async def test_get_download_url(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/download/file/10/url",
        payload={"url": "https://cdn.seedr.cc/dl/token/file.mkv"},
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


async def test_get_archive_bytes(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/download/archive/abc123",
        body=b"PK\x03\x04",
    )
    async with token_client:
        data = await token_client.downloads.get_archive_bytes("abc123")
    assert data[:2] == b"PK"
