"""Tests for AccountResource (formerly UserResource)."""

from __future__ import annotations

import pytest
from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from seedr_api.exceptions import AuthenticationError
from tests.conftest import API_BASE

SETTINGS_RESPONSE = {
    "subtitles_language": "eng",
    "site_language": "en",
    "email_newsletter": 0,
    "email_announcements": 0,
    "email_task_notifications_enabled": False,
    "select_files_on_task_add": 0,
    "userId": 3828843,
}

QUOTA_RESPONSE = {
    "bandwidth_used": 0,
    "bandwidth_max": 10737418240,
    "space_used": 1073741824,
    "space_max": 5368709120,
    "space_scope": "free",
    "is_premium": False,
}


async def test_get_settings(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(f"{API_BASE}/me/settings", payload=SETTINGS_RESPONSE)
    async with token_client:
        settings = await token_client.account.get_settings()
    assert settings.subtitles_language == "eng"
    assert settings.site_language == "en"
    assert settings.user_id == 3828843
    assert settings.email_newsletter == 0


async def test_get_quota(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/me/quota",
        payload=QUOTA_RESPONSE,
    )
    async with token_client:
        quota = await token_client.account.get_quota()
    assert quota.space_max == 5368709120
    assert quota.space_used == 1073741824
    assert quota.is_premium is False


async def test_get_wishlist(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/tasks/wishlist",
        payload=[
            {
                "id": 1,
                "user_id": 100,
                "title": "Big Movie",
                "size": 5000000,
                "torrent_hash": "abc",
                "torrent_magnet": "magnet:?xt=abc",
                "created": "2024-01-01",
                "added": 1704067200,
                "is_private": 0,
            }
        ],
    )
    async with token_client:
        wishlist = await token_client.account.get_wishlist()
    assert len(wishlist) == 1
    assert wishlist[0].title == "Big Movie"


async def test_get_wishlist_empty_returns_empty_list(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/tasks/wishlist",
        status=404,
        payload={"status_code": 404, "reason_phrase": "Not Found"},
    )
    async with token_client:
        wishlist = await token_client.account.get_wishlist()
    assert wishlist == []


async def test_delete_wishlist_item(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.delete(
        f"{API_BASE}/tasks/wishlist/1",
        payload={"success": True},
    )
    async with token_client:
        result = await token_client.account.delete_wishlist_item(1)
    assert result is not None


async def test_get_settings_unauthorized(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/me/settings",
        status=401,
        payload={"status_code": 401, "reason_phrase": "Invalid or expired token"},
    )
    async with token_client:
        with pytest.raises(AuthenticationError):
            await token_client.account.get_settings()
