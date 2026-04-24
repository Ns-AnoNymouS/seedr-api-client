"""Integration tests — UserResource."""

from seedr_api.client import SeedrClient
from seedr_api.models.user import Quota, UserInfo, UserSettings


async def test_get_user(client: SeedrClient) -> None:
    user = await client.user.get()
    assert isinstance(user, UserInfo)
    assert isinstance(user.id, int)
    assert isinstance(user.email, str)
    assert "@" in user.email


async def test_get_quota(client: SeedrClient) -> None:
    quota = await client.user.get_quota()
    assert isinstance(quota, Quota)
    assert isinstance(quota.space_max, int)
    assert isinstance(quota.space_used, int)
    assert quota.space_max > 0
    assert 0 <= quota.space_used <= quota.space_max


async def test_get_settings(client: SeedrClient) -> None:
    settings = await client.user.get_settings()
    assert isinstance(settings, UserSettings)
    assert isinstance(settings.settings, dict)
    assert len(settings.settings) > 0
