"""Tests for FilesystemResource."""

import pytest
from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from seedr_api.exceptions import NotFoundError
from tests.conftest import API_BASE

FOLDER_INFO = {"id": 1, "path": "root", "size": 1024}
FOLDER_CONTENTS = {
    "id": 1,
    "path": "root",
    "size": 2048,
    "folders": [{"id": 2, "path": "Movies", "size": 512}],
    "files": [{"id": 10, "name": "readme.txt", "size": 100, "hash": "abc"}],
    "torrents": [],
    "tasks": [],
}
FILE_INFO = {"id": 10, "name": "readme.txt", "size": 100, "hash": "abc"}


async def test_get_root(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{API_BASE}/fs/root", payload=FOLDER_INFO)
    async with token_client:
        result = await token_client.filesystem.get_root()
    assert result.id == 1
    assert result.path == "root"


async def test_list_root_contents(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{API_BASE}/fs/root/contents", payload=FOLDER_CONTENTS)
    async with token_client:
        result = await token_client.filesystem.list_root_contents()
    assert len(result.folders) == 1
    assert result.folders[0].path == "Movies"
    assert len(result.files) == 1
    assert result.files[0].name == "readme.txt"


async def test_get_folder(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/fs/folder/2", payload={"id": 2, "path": "Movies", "size": 512}
    )
    async with token_client:
        result = await token_client.filesystem.get_folder(2)
    assert result.id == 2
    assert result.path == "Movies"


async def test_list_folder_contents(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/fs/folder/2/contents", payload=FOLDER_CONTENTS
    )
    async with token_client:
        result = await token_client.filesystem.list_folder_contents(2)
    assert len(result.files) == 1


async def test_get_file(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{API_BASE}/fs/file/10", payload=FILE_INFO)
    async with token_client:
        result = await token_client.filesystem.get_file(10)
    assert result.id == 10
    assert result.name == "readme.txt"


async def test_get_file_not_found(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/fs/file/999", status=404, payload={"error": "Not found"}
    )
    async with token_client:
        with pytest.raises(NotFoundError):
            await token_client.filesystem.get_file(999)


async def test_create_folder(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/fs/folder", payload={"id": 5, "path": "New Folder", "size": 0}
    )
    async with token_client:
        result = await token_client.filesystem.create_folder("New Folder")
    assert result.id == 5
    assert result.path == "New Folder"


async def test_create_folder_with_parent(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/fs/folder", payload={"id": 6, "path": "Sub", "size": 0}
    )
    async with token_client:
        result = await token_client.filesystem.create_folder("Sub", parent_id=2)
    assert result.id == 6


async def test_delete_folder(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.delete(
        f"{API_BASE}/fs/folder/2", payload={"success": True}
    )
    async with token_client:
        await token_client.filesystem.delete_folder(2)


async def test_delete_file(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.delete(
        f"{API_BASE}/fs/file/10", payload={"success": True}
    )
    async with token_client:
        await token_client.filesystem.delete_file(10)


async def test_batch_delete(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/fs/batch/delete", payload={"success": True, "errors": []}
    )
    async with token_client:
        result = await token_client.filesystem.batch_delete([1, 2, 3])
    assert result.success is True


async def test_batch_copy(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/fs/batch/copy", payload={"success": True, "errors": []}
    )
    async with token_client:
        result = await token_client.filesystem.batch_copy([1, 2], destination_folder_id=5)
    assert result.success is True


async def test_batch_move(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/fs/batch/move", payload={"success": True, "errors": []}
    )
    async with token_client:
        result = await token_client.filesystem.batch_move([1, 2], destination_folder_id=5)
    assert result.success is True
