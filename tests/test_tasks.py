"""Tests for TasksResource against the V2 adapter."""

from __future__ import annotations

from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from seedr_api.exceptions import InsufficientSpaceError
from tests.conftest import API_BASE

# Real POST /tasks response shape: {user_torrent_id, title, success, torrent_hash}
ADD_TASK_RESPONSE = {
    "user_torrent_id": 42,
    "title": "ubuntu.iso",
    "success": True,
    "torrent_hash": "abc123",
}

TASK = {
    "id": 42,
    "name": "ubuntu.iso",
    "progress": 55.0,
    "size": 1_000_000,
    "state": "downloading",
    "created_at": "2026-01-01 00:00:00",
    "user_id": 1,
    "type": "torrent",
}


async def test_list_tasks(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{API_BASE}/tasks", payload={"tasks": [TASK], "user_id": 1})
    async with token_client:
        result = await token_client.tasks.list()
    assert isinstance(result.tasks, list)
    assert len(result.tasks) == 1
    assert result.tasks[0].id == 42
    assert result.tasks[0].name == "ubuntu.iso"


async def test_add_magnet(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(f"{API_BASE}/tasks", payload=ADD_TASK_RESPONSE)
    async with token_client:
        task = await token_client.tasks.add_magnet("magnet:?xt=urn:btih:abc")
    assert task.user_torrent_id == 42
    assert task.id == 42  # property
    assert task.title == "ubuntu.iso"
    assert task.name == "ubuntu.iso"  # property
    assert task.state == "added"  # property
    assert task.torrent_hash == "abc123"


async def test_add_magnet_with_folder_id(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(f"{API_BASE}/tasks", payload=ADD_TASK_RESPONSE)
    async with token_client:
        task = await token_client.tasks.add_magnet("magnet:?xt=urn:btih:abc", folder_id=5)
    assert task.user_torrent_id == 42


async def test_add_from_wishlist(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(f"{API_BASE}/tasks", payload=ADD_TASK_RESPONSE)
    async with token_client:
        task = await token_client.tasks.add_from_wishlist(wishlist_id=99)
    assert task.user_torrent_id == 42


async def test_add_magnet_not_enough_space(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    wt = {"id": 1, "title": "Big Movie", "torrent_hash": "abc"}
    mock_aioresponses.post(
        f"{API_BASE}/tasks",
        status=413,
        payload={"reason_phrase": "not_enough_space_added_to_wishlist", "wt": wt},
    )
    async with token_client:
        try:
            await token_client.tasks.add_magnet("magnet:?xt=urn:btih:big")
            raise AssertionError("Expected InsufficientSpaceError")
        except InsufficientSpaceError as exc:
            assert exc.wishlist_item == wt
            assert exc.status_code == 413


async def test_delete_torrent(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.delete(
        f"{API_BASE}/tasks/42",
        payload={"success": True},
    )
    async with token_client:
        result = await token_client.tasks.delete_torrent(42)
    assert result.success is True


async def test_delete_task(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.delete(
        f"{API_BASE}/tasks/42",
        payload={"success": True},
    )
    async with token_client:
        result = await token_client.tasks.delete(42)
    assert result.success is True
