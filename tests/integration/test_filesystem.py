"""Integration tests — FilesystemResource."""

from __future__ import annotations

import time

import pytest

from seedr_api.client import SeedrClient
from seedr_api.models.filesystem import FileInfo, FolderContents, FolderInfo


async def test_get_root(client: SeedrClient) -> None:
    root = await client.filesystem.get_root()
    assert isinstance(root, FolderInfo)
    assert isinstance(root.id, int)


async def test_list_root_contents(client: SeedrClient) -> None:
    contents = await client.filesystem.list_root_contents()
    assert isinstance(contents, FolderContents)
    assert isinstance(contents.id, int)
    assert isinstance(contents.folders, list)
    assert isinstance(contents.files, list)
    assert isinstance(contents.torrents, list)
    for f in contents.folders:
        assert isinstance(f, FolderInfo)
        assert isinstance(f.id, int)
    for f in contents.files:
        assert isinstance(f, FileInfo)
        assert isinstance(f.id, int)


async def test_get_folder(client: SeedrClient) -> None:
    contents = await client.filesystem.list_root_contents()
    if not contents.folders:
        pytest.skip("No folders in root")
    folder = await client.filesystem.get_folder(contents.folders[0].id)
    assert isinstance(folder, FolderInfo)
    assert folder.id == contents.folders[0].id
    assert isinstance(folder.path, str)


async def test_list_folder_contents(client: SeedrClient) -> None:
    contents = await client.filesystem.list_root_contents()
    if not contents.folders:
        pytest.skip("No folders in root")
    inner = await client.filesystem.list_folder_contents(contents.folders[0].id)
    assert isinstance(inner, FolderContents)
    assert isinstance(inner.folders, list)
    assert isinstance(inner.files, list)


async def test_get_file(client: SeedrClient) -> None:
    contents = await client.filesystem.list_root_contents()
    file_id: int | None = None
    for folder in contents.folders:
        inner = await client.filesystem.list_folder_contents(folder.id)
        if inner.files:
            file_id = inner.files[0].id
            break
    if file_id is None:
        pytest.skip("No files available")

    file_info = await client.filesystem.get_file(file_id)
    assert isinstance(file_info, FileInfo)
    assert file_info.id == file_id
    assert isinstance(file_info.name, str)
    assert len(file_info.name) > 0
    assert isinstance(file_info.size, int)
    assert file_info.size >= 0


async def test_create_and_delete_folder(client: SeedrClient) -> None:
    name = f"_ci_test_{int(time.time())}"
    folder = await client.filesystem.create_folder(name)
    assert isinstance(folder, FolderInfo)
    assert isinstance(folder.id, int)

    # Confirm it appears in root
    contents = await client.filesystem.list_root_contents()
    assert folder.id in [f.id for f in contents.folders]

    # Delete should not raise
    await client.filesystem.delete_folder(folder.id)
