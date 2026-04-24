"""Tests for FilesystemResource."""

import pytest
from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from seedr_api.exceptions import NotFoundError

OAUTH_BASE = "https://www.seedr.cc/api/v0.1"

FOLDER_INFO = {"id": 1, "name": "root", "size": 1024}
FOLDER_CONTENTS = {
    "id": 1,
    "name": "root",
    "size": 2048,
    "folders": [{"id": 2, "name": "Movies", "size": 512}],
    "files": [{"id": 10, "name": "readme.txt", "size": 100, "hash": "abc"}],
    "torrents": [],
}
FILE_INFO = {"id": 10, "name": "readme.txt", "size": 100, "hash": "abc"}


@pytest.mark.asyncio
async def test_get_root(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{OAUTH_BASE}/fs/root", payload=FOLDER_INFO)
    async with token_client:
        result = await token_client.filesystem.get_root()
    assert result.id == 1
    assert result.name == "root"


@pytest.mark.asyncio
async def test_list_root_contents(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{OAUTH_BASE}/fs/root/contents", payload=FOLDER_CONTENTS)
    async with token_client:
        result = await token_client.filesystem.list_root_contents()
    assert len(result.folders) == 1
    assert result.folders[0].name == "Movies"
    assert len(result.files) == 1


@pytest.mark.asyncio
async def test_get_folder(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{OAUTH_BASE}/fs/folder/2", payload={"id": 2, "name": "Movies", "size": 512}
    )
    async with token_client:
        result = await token_client.filesystem.get_folder(2)
    assert result.id == 2


@pytest.mark.asyncio
async def test_get_file(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{OAUTH_BASE}/fs/file/10", payload=FILE_INFO)
    async with token_client:
        result = await token_client.filesystem.get_file(10)
    assert result.id == 10
    assert result.name == "readme.txt"


@pytest.mark.asyncio
async def test_get_file_not_found(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{OAUTH_BASE}/fs/file/999", status=404, payload={"error": "Not found"}
    )
    async with token_client:
        with pytest.raises(NotFoundError):
            await token_client.filesystem.get_file(999)


@pytest.mark.asyncio
async def test_create_folder(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{OAUTH_BASE}/fs/folder", payload={"id": 5, "name": "New Folder", "size": 0}
    )
    async with token_client:
        result = await token_client.filesystem.create_folder("New Folder")
    assert result.name == "New Folder"


@pytest.mark.asyncio
async def test_delete_folder(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.delete(f"{OAUTH_BASE}/fs/folder/2", status=204)
    async with token_client:
        await token_client.filesystem.delete_folder(2)  # Should not raise


@pytest.mark.asyncio
async def test_delete_file(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.delete(f"{OAUTH_BASE}/fs/file/10", status=204)
    async with token_client:
        await token_client.filesystem.delete_file(10)


@pytest.mark.asyncio
async def test_batch_delete(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{OAUTH_BASE}/fs/batch/delete", payload={"success": True, "errors": []}
    )
    async with token_client:
        result = await token_client.filesystem.batch_delete([1, 2, 3])
    assert result.success is True
