"""Tests for AuthResource."""

import pytest
from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from seedr_api.exceptions import APIError
from tests.conftest import API_BASE, DEVICE_CODE_URL, DEVICE_TOKEN_URL


async def test_get_apps(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/oauth/apps",
        payload={"apps": [{"client_id": "abc123", "name": "TestApp"}]},
    )
    async with token_client:
        apps = await token_client.auth.get_apps()
    assert len(apps) == 1
    assert apps[0].client_id == "abc123"
    assert apps[0].name == "TestApp"


async def test_get_apps_list_response(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/oauth/apps",
        payload=[{"client_id": "xyz", "name": "App2"}],
    )
    async with token_client:
        apps = await token_client.auth.get_apps()
    assert apps[0].client_id == "xyz"


async def test_exchange_code(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/oauth/token",
        payload={"access_token": "tok", "token_type": "Bearer"},
    )
    async with token_client:
        resp = await token_client.auth.exchange_code(
            client_id="id",
            client_secret="secret",
            code="code123",
            redirect_uri="https://example.com/callback",
        )
    assert resp.access_token == "tok"


async def test_refresh_token(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/oauth/token",
        payload={"access_token": "newtok", "token_type": "Bearer"},
    )
    async with token_client:
        resp = await token_client.auth.refresh_token(
            client_id="id",
            client_secret="secret",
            refresh_token="oldrefresh",
        )
    assert resp.access_token == "newtok"


async def test_request_device_code(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        DEVICE_CODE_URL,
        payload={
            "device_code": "devcode",
            "user_code": "USER-CODE",
            "verification_uri": "https://v2.seedr.cc/api/v0.1/p/oauth/device/verify",
            "expires_in": 300,
            "interval": 5,
        },
    )
    async with token_client:
        dc = await token_client.auth.request_device_code(client_id="id")
    assert dc.user_code == "USER-CODE"
    assert dc.device_code == "devcode"


async def test_request_device_code_fixes_relative_verification_uri(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        DEVICE_CODE_URL,
        payload={
            "device_code": "dev",
            "user_code": "CODE",
            "verification_uri": "/api/v0.1/p/oauth/device/verify",
            "expires_in": 300,
            "interval": 5,
        },
    )
    async with token_client:
        dc = await token_client.auth.request_device_code(client_id="id")
    assert dc.verification_uri.startswith("https://")


async def test_revoke_token(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(f"{API_BASE}/oauth/token/revoke_rfc7009", payload={})
    async with token_client:
        await token_client.auth.revoke_token(token="sometoken")


async def test_poll_device_token_success(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        DEVICE_TOKEN_URL,
        payload={"access_token": "devicetok", "token_type": "Bearer"},
    )
    async with token_client:
        resp = await token_client.auth.poll_device_token(
            client_id="id",
            device_code="devcode",
            interval=0,
            max_wait=10,
        )
    assert resp.access_token == "devicetok"


async def test_poll_device_token_denied(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        DEVICE_TOKEN_URL,
        status=400,
        payload={"error": "access_denied"},
    )
    async with token_client:
        with pytest.raises(APIError):
            await token_client.auth.poll_device_token(
                client_id="id",
                device_code="devcode",
                interval=0,
                max_wait=1,
            )


async def test_exchange_client_credentials(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.post(
        f"{API_BASE}/oauth/token",
        payload={"access_token": "server_token", "token_type": "Bearer"},
    )
    async with token_client:
        resp = await token_client.auth.exchange_client_credentials(
            client_id="server_id",
            client_secret="server_secret",
        )
    assert resp.access_token == "server_token"


def test_generate_pkce_challenge(token_client: SeedrClient) -> None:
    pkce = token_client.auth.generate_pkce_challenge(64)
    assert len(pkce.code_verifier) == 64
    assert len(pkce.code_challenge) > 10
    assert pkce.code_challenge_method == "S256"

    with pytest.raises(ValueError, match="length must be between 43 and 128"):
        token_client.auth.generate_pkce_challenge(10)


def test_generate_authorize_url(token_client: SeedrClient) -> None:
    url_obj = token_client.auth.generate_authorize_url(
        client_id="myclient",
        redirect_uri="https://local",
        scope="files.read",
        state="xyz",
    )
    assert "oauth/authorize" in url_obj.url
    assert "client_id=myclient" in url_obj.url
    assert "state=xyz" in url_obj.url
    assert url_obj.pkce is None


def test_generate_pkce_authorize_url(token_client: SeedrClient) -> None:
    url_obj = token_client.auth.generate_pkce_authorize_url(
        client_id="pkceclient",
        redirect_uri="https://local",
    )
    assert "code_challenge=" in url_obj.url
    assert "code_challenge_method=S256" in url_obj.url
    assert url_obj.pkce is not None
    assert url_obj.pkce.code_verifier
