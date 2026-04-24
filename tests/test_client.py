"""Tests for SeedrClient — lifecycle and factory constructors."""

import pytest
from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from tests.conftest import API_BASE


async def test_context_manager_closes_session(mock_aioresponses: aioresponses) -> None:
    async with SeedrClient.from_token("tok") as client:
        assert client._http._session is None or not client._http._session.closed
    if client._http._session is not None:
        assert client._http._session.closed


async def test_from_token_uses_api_base() -> None:
    client = SeedrClient.from_token("tok")
    assert client._http._base_url == API_BASE
    assert client._http._access_token == "tok"
    await client.close()


async def test_from_credentials_uses_api_base() -> None:
    client = SeedrClient.from_credentials("a@b.com", "pass")
    assert client._http._base_url == API_BASE
    assert client._http._basic_auth == ("a@b.com", "pass")
    await client.close()


def test_resource_accessors_return_correct_types(token_client: SeedrClient) -> None:
    from seedr_api.resources.auth import AuthResource
    from seedr_api.resources.downloads import DownloadsResource
    from seedr_api.resources.filesystem import FilesystemResource
    from seedr_api.resources.presentations import PresentationsResource
    from seedr_api.resources.search import SearchResource
    from seedr_api.resources.subtitles import SubtitlesResource
    from seedr_api.resources.tasks import TasksResource
    from seedr_api.resources.user import UserResource

    assert isinstance(token_client.auth, AuthResource)
    assert isinstance(token_client.filesystem, FilesystemResource)
    assert isinstance(token_client.tasks, TasksResource)
    assert isinstance(token_client.downloads, DownloadsResource)
    assert isinstance(token_client.presentations, PresentationsResource)
    assert isinstance(token_client.subtitles, SubtitlesResource)
    assert isinstance(token_client.search, SearchResource)
    assert isinstance(token_client.user, UserResource)


def test_resource_accessors_are_cached(token_client: SeedrClient) -> None:
    assert token_client.filesystem is token_client.filesystem
    assert token_client.tasks is token_client.tasks


def test_update_token(token_client: SeedrClient) -> None:
    token_client.update_token("new-token")
    assert token_client._http._access_token == "new-token"


@pytest.mark.asyncio
async def test_login_with_client_credentials(mock_aioresponses: aioresponses) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/oauth/token",
        payload={"access_token": "s2s_token", "token_type": "Bearer"},
    )
    client = await SeedrClient.login_with_client_credentials("id", "secret")
    assert client._http._access_token == "s2s_token"
    await client.close()
