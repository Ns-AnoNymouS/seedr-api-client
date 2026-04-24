"""Tests for TasksResource."""

from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from tests.conftest import API_BASE

TASK = {
    "id": 42,
    "name": "ubuntu.iso",
    "progress": 55.0,
    "size": 1_000_000,
    "state": "downloading",
    "created_at": "2026-01-01 00:00:00",
}

TASK_ENVELOPE = {"task": TASK, "success": True}


async def test_list_tasks(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{API_BASE}/tasks", payload={"tasks": [TASK]})
    async with token_client:
        tasks = await token_client.tasks.list()
    assert len(tasks) == 1
    assert tasks[0].id == 42


async def test_list_tasks_list_response(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{API_BASE}/tasks", payload=[TASK])
    async with token_client:
        tasks = await token_client.tasks.list()
    assert tasks[0].state == "downloading"


async def test_get_task(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{API_BASE}/tasks/42", payload=TASK_ENVELOPE)
    async with token_client:
        task = await token_client.tasks.get(42)
    assert task.name == "ubuntu.iso"
    assert task.progress == 55.0
    assert task.state == "downloading"


async def test_add_magnet(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(f"{API_BASE}/tasks", payload=TASK)
    async with token_client:
        task = await token_client.tasks.add_magnet("magnet:?xt=urn:btih:abc")
    assert task.id == 42


async def test_add_url(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(f"{API_BASE}/tasks", payload=TASK)
    async with token_client:
        task = await token_client.tasks.add_url("http://example.com/file.torrent")
    assert task.id == 42


async def test_pause_task(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(f"{API_BASE}/tasks/42/pause", payload={})
    async with token_client:
        await token_client.tasks.pause(42)


async def test_resume_task(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(f"{API_BASE}/tasks/42/resume", payload={})
    async with token_client:
        await token_client.tasks.resume(42)


async def test_delete_task(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.delete(f"{API_BASE}/tasks/42", status=204)
    async with token_client:
        await token_client.tasks.delete(42)
