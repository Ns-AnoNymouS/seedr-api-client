"""Tests for V2 model properties and client/session helpers."""

from __future__ import annotations

from seedr_api.client import SeedrClient
from seedr_api.core.token import Token
from seedr_api.models.v2.account import V2AccountInfo, _V2UserStorageInfo
from seedr_api.models.v2.tasks import V2AddTaskResult, V2Task

# ---------------------------------------------------------------------------
# V2Task properties
# ---------------------------------------------------------------------------


def test_v2_task_title_property() -> None:
    task = V2Task(name="ubuntu.iso")
    assert task.title == "ubuntu.iso"


def test_v2_task_torrent_hash_from_payload() -> None:
    task = V2Task(torrent_payload={"hash": "abc123", "other": "x"})
    assert task.torrent_hash == "abc123"


def test_v2_task_torrent_hash_no_payload() -> None:
    task = V2Task()
    assert task.torrent_hash is None


# ---------------------------------------------------------------------------
# V2AddTaskResult.state property
# ---------------------------------------------------------------------------


def test_add_task_result_state_wishlist() -> None:
    result = V2AddTaskResult(wt={"id": 1, "title": "Movie"})
    assert result.state == "wishlist"


def test_add_task_result_state_added() -> None:
    result = V2AddTaskResult(success=True)
    assert result.state == "added"


def test_add_task_result_state_none() -> None:
    result = V2AddTaskResult(success=False)
    assert result.state is None


# ---------------------------------------------------------------------------
# V2AccountInfo properties
# ---------------------------------------------------------------------------


def test_v2_account_info_properties_populated() -> None:
    info = V2AccountInfo.model_validate(
        {
            "profile": {"id": 42, "email": "user@example.com"},
            "account": {
                "is_premium": False,
                "storage": {"limit": 5368709120, "used": 1073741824},
            },
        }
    )
    assert info.email == "user@example.com"
    assert info.id == 42
    assert info.storage is not None
    assert info.storage.limit == 5368709120
    assert info.storage.max == 5368709120


def test_v2_account_info_properties_no_profile() -> None:
    info = V2AccountInfo()
    assert info.email is None
    assert info.id is None
    assert info.storage is None


def test_v2_storage_info_max_property() -> None:
    storage = _V2UserStorageInfo(limit=1024, used=512)
    assert storage.max == 1024


# ---------------------------------------------------------------------------
# SeedrClient helpers
# ---------------------------------------------------------------------------


def test_client_repr() -> None:
    client = SeedrClient.from_token("tok")
    r = repr(client)
    assert "SeedrClient" in r


def test_client_access_token() -> None:
    client = SeedrClient.from_token("my-token")
    assert client.access_token == "my-token"


# ---------------------------------------------------------------------------
# SeedrSession
# ---------------------------------------------------------------------------


async def test_session_from_token_properties() -> None:
    from seedr_api.session import SeedrSession

    token = Token(access_token="tok", refresh_token="ref", client_id="seedr_chrome")
    session = await SeedrSession.from_token(token)
    assert session.token is token
    assert session.client is not None
    assert "SeedrSession" in repr(session)


async def test_session_context_manager() -> None:
    from seedr_api.session import SeedrSession

    token = Token(access_token="tok")
    session = await SeedrSession.from_token(token)
    async with session as s:
        assert s is session
