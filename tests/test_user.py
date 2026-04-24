"""Tests for UserResource."""

import pytest
from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from seedr_api.exceptions import AuthenticationError

OAUTH_BASE = "https://www.seedr.cc/api/v0.1"


@pytest.mark.asyncio
async def test_get_user(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{OAUTH_BASE}/user",
        payload={
            "id": 1,
            "username": "naveen",
            "email": "naveen@example.com",
            "package_name": "Pro",
        },
    )
    async with token_client:
        user = await token_client.user.get()
    assert user.username == "naveen"
    assert user.email == "naveen@example.com"


@pytest.mark.asyncio
async def test_get_quota(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{OAUTH_BASE}/me/quota",
        payload={"space_max": 107374182400, "space_used": 5368709120},
    )
    async with token_client:
        quota = await token_client.user.get_quota()
    assert quota.space_max == 107374182400
    assert quota.space_used == 5368709120


@pytest.mark.asyncio
async def test_get_settings(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{OAUTH_BASE}/me/settings",
        payload={"autoplay": True, "quality": "1080p"},
    )
    async with token_client:
        settings = await token_client.user.get_settings()
    assert settings.settings.get("autoplay") is True


@pytest.mark.asyncio
async def test_get_user_unauthorized(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{OAUTH_BASE}/user", status=401, payload={"error": "Unauthorized"}
    )
    async with token_client:
        with pytest.raises(AuthenticationError):
            await token_client.user.get()
