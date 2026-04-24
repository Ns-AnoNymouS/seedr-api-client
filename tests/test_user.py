"""Tests for UserResource."""

import pytest
from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from seedr_api.exceptions import AuthenticationError
from tests.conftest import API_BASE

USER_RESPONSE = {
    "profile": {
        "id": 1,
        "username": "naveen",
        "email": "naveen@example.com",
        "created_at": 1618334040,
        "last_login": 1777048247,
    },
    "account": {
        "is_premium": False,
        "storage": {"limit": 4294967296, "used": 1024},
    },
}


async def test_get_user(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{API_BASE}/user", payload=USER_RESPONSE)
    async with token_client:
        user = await token_client.user.get()
    assert user.id == 1
    assert user.username == "naveen"
    assert user.email == "naveen@example.com"


async def test_get_user_flat_response(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    """If the API returns a flat dict (no profile key), it should still parse."""
    mock_aioresponses.get(
        f"{API_BASE}/user",
        payload={"id": 2, "username": "test", "email": "t@t.com"},
    )
    async with token_client:
        user = await token_client.user.get()
    assert user.id == 2


async def test_get_quota(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/me/quota",
        payload={
            "space_max": 4294967296,
            "space_used": 1073741824,
            "bandwidth_max": 0,
            "bandwidth_used": 0,
        },
    )
    async with token_client:
        quota = await token_client.user.get_quota()
    assert quota.space_max == 4294967296
    assert quota.space_used == 1073741824


async def test_get_settings(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/me/settings",
        payload={"autoplay": True, "quality": "1080p"},
    )
    async with token_client:
        settings = await token_client.user.get_settings()
    assert settings.settings.get("autoplay") is True


async def test_get_user_unauthorized(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/user", status=401, payload={"error": "Unauthorized"}
    )
    async with token_client:
        with pytest.raises(AuthenticationError):
            await token_client.user.get()
