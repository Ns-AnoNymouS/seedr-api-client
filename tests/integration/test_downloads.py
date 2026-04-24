"""Integration tests — DownloadsResource."""

from __future__ import annotations

import pytest

from seedr_api.client import SeedrClient


async def _first_file_id(client: SeedrClient) -> int | None:
    contents = await client.filesystem.list_root_contents()
    for folder in contents.folders:
        inner = await client.filesystem.list_folder_contents(folder.id)
        if inner.files:
            return inner.files[0].id
    return None


async def test_get_download_url(client: SeedrClient) -> None:
    file_id = await _first_file_id(client)
    if file_id is None:
        pytest.skip("No files available")
    url = await client.downloads.get_download_url(file_id)
    assert isinstance(url, str)
    assert url.startswith("https://")


async def test_stream_file(client: SeedrClient) -> None:
    file_id = await _first_file_id(client)
    if file_id is None:
        pytest.skip("No files available")
    received = 0
    async with client.downloads.stream_file(file_id, chunk_size=65536) as stream:
        async for chunk in stream:
            assert isinstance(chunk, bytes)
            assert len(chunk) > 0
            received += len(chunk)
            if received >= 64 * 1024:
                break
    assert received > 0
