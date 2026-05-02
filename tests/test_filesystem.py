"""Tests for FilesystemResource against the V2 adapter."""

from __future__ import annotations

import pytest
from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from seedr_api.exceptions import NotFoundError
from tests.conftest import API_BASE

FOLDER_CONTENTS = {
    "id": 167483733,
    "path": "",
    "size": 2048,
    "space_max": 5368709120,
    "space_used": 1073741824,
    "space_scope": "premium",
    "saw_walkthrough": 1,
    "timestamp": "2024-01-01T00:00:00Z",
    "parent": -1,
    "folders": [{"id": 2, "path": "Movies", "size": 512, "last_update": "2024-01-01"}],
    "files": [{"id": 10, "name": "readme.txt", "size": 100, "hash": "abc"}],
    "torrents": [],
    "tasks": [],
}

FILE_INFO = {"id": 10, "name": "readme.txt", "size": 100, "hash": "abc"}


async def test_list_root_contents(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{API_BASE}/fs/root/contents", payload=FOLDER_CONTENTS)
    async with token_client:
        result = await token_client.filesystem.list_root_contents()
    assert len(result.folders) == 1
    assert result.folders[0].path == "Movies"
    assert result.folders[0].name == "Movies"  # property
    assert len(result.files) == 1
    assert result.files[0].name == "readme.txt"


async def test_get_folder(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/fs/folder/2",
        payload={"id": 2, "path": "Movies", "size": 512},
    )
    async with token_client:
        result = await token_client.filesystem.get_folder(2)
    assert result.id == 2
    assert result.path == "Movies"


async def test_list_folder_contents(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{API_BASE}/fs/folder/2/contents", payload=FOLDER_CONTENTS)
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
        f"{API_BASE}/fs/file/999",
        status=404,
        payload={"status_code": 404, "reason_phrase": "File not found"},
    )
    async with token_client:
        with pytest.raises(NotFoundError):
            await token_client.filesystem.get_file(999)


async def test_create_folder(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/fs/folder",
        payload={"success": True, "id": "5", "path": "New Folder"},
    )
    async with token_client:
        result = await token_client.filesystem.create_folder("New Folder")
    assert result.id == 5
    assert result.path == "New Folder"
    assert result.name == "New Folder"  # property
    assert result.success is True


async def test_create_folder_with_parent(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/fs/folder",
        payload={"success": True, "id": "6", "path": "Sub"},
    )
    async with token_client:
        result = await token_client.filesystem.create_folder("Sub", parent_id=2)
    assert result.id == 6
    assert result.path == "Sub"


async def test_rename_folder_raises_not_implemented(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    async with token_client:
        with pytest.raises(NotImplementedError):
            await token_client.filesystem.rename_folder(2, "New Name")


async def test_rename_file_raises_not_implemented(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    async with token_client:
        with pytest.raises(NotImplementedError):
            await token_client.filesystem.rename_file(10, "new_name.txt")


async def test_delete_folder(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/fs/batch/delete",
        payload={"success": True},
    )
    async with token_client:
        result = await token_client.filesystem.delete_folder(2)
    assert result is not None


async def test_delete_file(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/fs/batch/delete",
        payload={"success": True},
    )
    async with token_client:
        result = await token_client.filesystem.delete_file(10)
    assert result is not None


async def test_batch_delete(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(f"{API_BASE}/fs/batch/delete", payload={"success": True})
    async with token_client:
        result = await token_client.filesystem.batch_delete(
            [{"type": "folder", "id": 1}, {"type": "folder_file", "id": 2}]
        )
    assert result is not None
