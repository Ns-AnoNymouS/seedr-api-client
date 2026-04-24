"""Integration tests — PresentationsResource."""

from __future__ import annotations

import pytest

from seedr_api.client import SeedrClient
from seedr_api.models.media import FilePresentations, FolderPresentations


async def _first_folder_and_file(client: SeedrClient) -> tuple[int | None, int | None]:
    contents = await client.filesystem.list_root_contents()
    folder_id = contents.folders[0].id if contents.folders else None
    file_id: int | None = None
    for folder in contents.folders:
        inner = await client.filesystem.list_folder_contents(folder.id)
        if inner.files:
            file_id = inner.files[0].id
            break
    return folder_id, file_id


async def test_get_folder_presentations(client: SeedrClient) -> None:
    folder_id, _ = await _first_folder_and_file(client)
    if folder_id is None:
        pytest.skip("No folders available")
    fp = await client.presentations.get_folder_presentations(folder_id)
    assert isinstance(fp, FolderPresentations)
    assert isinstance(fp.files, list)
    assert isinstance(fp.total_files, int)
    assert fp.total_files >= 0
    for item in fp.files:
        assert isinstance(item, FilePresentations)
        assert isinstance(item.presentations, dict)


async def test_get_file_presentation_thumbnail(client: SeedrClient) -> None:
    _, file_id = await _first_folder_and_file(client)
    if file_id is None:
        pytest.skip("No files available")
    urls = await client.presentations.get_file_presentation(file_id, "thumbnail")
    assert isinstance(urls, dict)
    assert len(urls) > 0
    for size, url in urls.items():
        assert isinstance(size, str)
        assert isinstance(url, str)
        assert url.startswith("https://")
