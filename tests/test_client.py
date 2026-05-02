"""Tests for SeedrClient — lifecycle and factory constructors."""

from __future__ import annotations

import pytest
from aioresponses import aioresponses

from seedr_api import SeedrClientBuilder
from seedr_api.adapters.auto import AutoAdapter
from seedr_api.adapters.v1 import V1Adapter
from seedr_api.adapters.v2 import V2Adapter
from seedr_api.client import SeedrClient
from seedr_api.core.token_storage import MemoryTokenStorage


async def test_context_manager_closes_session(mock_aioresponses: aioresponses) -> None:
    async with SeedrClient.from_token("tok") as client:
        assert isinstance(client._adapter, V2Adapter)
    # After exit, session should be closed
    session = client._adapter._session
    if session is not None:
        assert session.closed


async def test_from_token_creates_v2_adapter() -> None:
    client = SeedrClient.from_token("tok")
    assert isinstance(client._adapter, V2Adapter)
    assert client._adapter._access_token == "tok"
    await client.close()


async def test_from_v1_token_creates_v1_adapter() -> None:
    client = SeedrClient.from_v1_token("tok")
    assert isinstance(client._adapter, V1Adapter)
    assert client._adapter._access_token == "tok"
    await client.close()


async def test_anonymous_creates_v1_adapter() -> None:
    client = SeedrClient.anonymous()
    assert isinstance(client._adapter, V1Adapter)
    await client.close()


async def test_from_tokens_creates_auto_adapter() -> None:
    client = SeedrClient.from_tokens(v1_token="t1", v2_token="t2")
    assert isinstance(client._adapter, AutoAdapter)
    assert client._adapter.v1 is not None
    assert client._adapter.v2 is not None
    await client.close()


def test_resource_accessors_return_correct_types(token_client: SeedrClient) -> None:
    from seedr_api.resources.account import AccountResource
    from seedr_api.resources.auth import AuthResource
    from seedr_api.resources.downloads import DownloadsResource
    from seedr_api.resources.filesystem import FilesystemResource
    from seedr_api.resources.presentations import PresentationsResource
    from seedr_api.resources.search import SearchResource
    from seedr_api.resources.subtitles import SubtitlesResource
    from seedr_api.resources.tasks import TasksResource

    assert isinstance(token_client.auth, AuthResource)
    assert isinstance(token_client.account, AccountResource)
    assert isinstance(token_client.filesystem, FilesystemResource)
    assert isinstance(token_client.tasks, TasksResource)
    assert isinstance(token_client.downloads, DownloadsResource)
    assert isinstance(token_client.presentations, PresentationsResource)
    assert isinstance(token_client.subtitles, SubtitlesResource)
    assert isinstance(token_client.search, SearchResource)


def test_resource_accessors_are_cached(token_client: SeedrClient) -> None:
    assert token_client.filesystem is token_client.filesystem
    assert token_client.tasks is token_client.tasks
    assert token_client.account is token_client.account


def test_update_token(token_client: SeedrClient) -> None:
    token_client.update_token("new-token")
    assert token_client._adapter._access_token == "new-token"


def test_builder_no_token_raises() -> None:
    with pytest.raises(ValueError, match="At least one token"):
        SeedrClientBuilder().build()


def test_builder_with_v2_token() -> None:
    client = SeedrClientBuilder().with_v2_token("access_tok").build()
    assert isinstance(client._adapter, V2Adapter)


def test_builder_with_v1_token() -> None:
    client = SeedrClientBuilder().with_v1_token("access_tok").build()
    assert isinstance(client._adapter, V1Adapter)


def test_builder_both_tokens_creates_auto() -> None:
    client = (
        SeedrClientBuilder()
        .with_v1_token("t1")
        .with_v2_token("t2")
        .build()
    )
    assert isinstance(client._adapter, AutoAdapter)


def test_builder_with_storage() -> None:
    storage = MemoryTokenStorage()
    client = (
        SeedrClientBuilder()
        .with_v2_token("tok")
        .with_token_storage(storage)
        .build()
    )
    assert isinstance(client._adapter, V2Adapter)


async def test_builder_with_refresh_token() -> None:
    refresh_called = []

    async def on_refresh(token: object) -> None:
        refresh_called.append(token)

    client = (
        SeedrClientBuilder()
        .with_v2_token("tok")
        .with_refresh_token("rt", client_id="seedr_chrome")
        .on_token_refresh(on_refresh)
        .build()
    )
    assert isinstance(client._adapter, V2Adapter)
    await client.close()
