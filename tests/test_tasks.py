"""Tests for TasksResource."""

import pytest
from aioresponses import aioresponses

from seedr_api.client import SeedrClient

OAUTH_BASE = "https://www.seedr.cc/api/v0.1"

TASK = {
    "id": 42,
    "name": "ubuntu.iso",
    "progress": 55.0,
    "size": 1_000_000,
    "status": "downloading",
}


@pytest.mark.asyncio
async def test_list_tasks(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{OAUTH_BASE}/tasks", payload=[TASK])
    async with token_client:
        tasks = await token_client.tasks.list()
    assert len(tasks) == 1
    assert tasks[0].id == 42


@pytest.mark.asyncio
async def test_get_task(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{OAUTH_BASE}/tasks/42", payload=TASK)
    async with token_client:
        task = await token_client.tasks.get(42)
    assert task.name == "ubuntu.iso"
    assert task.progress == 55.0


@pytest.mark.asyncio
async def test_add_magnet(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(f"{OAUTH_BASE}/tasks", payload=TASK)
    async with token_client:
        task = await token_client.tasks.add_magnet("magnet:?xt=urn:btih:abc")
    assert task.id == 42


@pytest.mark.asyncio
async def test_add_url(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(f"{OAUTH_BASE}/tasks", payload=TASK)
    async with token_client:
        task = await token_client.tasks.add_url("http://example.com/file.torrent")
    assert task.id == 42


@pytest.mark.asyncio
async def test_pause_task(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(f"{OAUTH_BASE}/tasks/42/pause", payload={})
    async with token_client:
        await token_client.tasks.pause(42)


@pytest.mark.asyncio
async def test_resume_task(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(f"{OAUTH_BASE}/tasks/42/resume", payload={})
    async with token_client:
        await token_client.tasks.resume(42)


@pytest.mark.asyncio
async def test_delete_task(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.delete(f"{OAUTH_BASE}/tasks/42", status=204)
    async with token_client:
        await token_client.tasks.delete(42)
