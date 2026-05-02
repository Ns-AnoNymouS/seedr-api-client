"""Tests for AuthResource — device code flow, PKCE helpers, token refresh."""

from __future__ import annotations

import pytest
from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from seedr_api.exceptions import APIError
from tests.conftest import API_BASE, DEVICE_CODE_URL, DEVICE_TOKEN_URL


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


def test_generate_pkce_challenge(token_client: SeedrClient) -> None:
    pkce = token_client.auth.generate_pkce_challenge(64)
    assert "code_verifier" in pkce
    assert len(pkce["code_verifier"]) == 64
    assert len(pkce["code_challenge"]) > 10
    assert pkce["code_challenge_method"] == "S256"

    with pytest.raises(ValueError, match="length must be between 43 and 128"):
        token_client.auth.generate_pkce_challenge(10)


def test_generate_authorize_url(token_client: SeedrClient) -> None:
    url = token_client.auth.generate_authorize_url(
        client_id="myclient",
        redirect_uri="https://local",
        scope="files.read",
        state="xyz",
    )
    assert "oauth/authorize" in url
    assert "client_id=myclient" in url
    assert "state=xyz" in url


def test_generate_pkce_authorize_url(token_client: SeedrClient) -> None:
    result = token_client.auth.generate_pkce_authorize_url(
        client_id="pkceclient",
        redirect_uri="https://local",
    )
    assert "code_challenge=" in result["url"]
    assert "code_challenge_method=S256" in result["url"]
    assert "code_verifier" in result
    assert result["code_verifier"]


async def test_v2_adapter_refresh_token(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    """Test that the V2 adapter's refresh_token method works correctly."""
    mock_aioresponses.post(
        f"{API_BASE}/oauth/token",
        payload={"access_token": "newtok", "token_type": "Bearer"},
    )
    from seedr_api.adapters.v2 import V2Adapter

    adapter = V2Adapter("old_token")
    async with adapter._get_session():
        pass  # ensure session created
    try:
        resp = await adapter.refresh_token("old_refresh", "seedr_chrome")
        assert resp.access_token == "newtok"
    finally:
        await adapter.close()
