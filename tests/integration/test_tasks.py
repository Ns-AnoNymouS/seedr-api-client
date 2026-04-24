"""Integration tests — TasksResource."""

import pytest

from seedr_api.client import SeedrClient
from seedr_api.models.tasks import Task


async def test_list_tasks(client: SeedrClient) -> None:
    tasks = await client.tasks.list()
    assert isinstance(tasks, list)
    for task in tasks:
        assert isinstance(task, Task)
        assert isinstance(task.id, int)
        assert isinstance(task.name, str)
        assert len(task.name) > 0


async def test_get_task(client: SeedrClient) -> None:
    tasks = await client.tasks.list()
    if not tasks:
        pytest.skip("No tasks available")
    task = await client.tasks.get(tasks[0].id)
    assert isinstance(task, Task)
    assert task.id == tasks[0].id
    assert isinstance(task.name, str)
    assert isinstance(task.state, str)
