"""Integration tests — SearchResource."""

from seedr_api.client import SeedrClient
from seedr_api.models.filesystem import FileInfo, FolderInfo


async def test_search_returns_results(client: SeedrClient) -> None:
    results = await client.search.search("a")
    assert isinstance(results, list)
    for item in results:
        assert isinstance(item, (FileInfo, FolderInfo))
        assert isinstance(item.id, int)


async def test_search_no_results(client: SeedrClient) -> None:
    results = await client.search.search("zzzzzzzz_no_match_xyzzy")
    assert isinstance(results, list)
