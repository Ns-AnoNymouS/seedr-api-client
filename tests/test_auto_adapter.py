"""Tests for AutoAdapter — routing and delegation to V1/V2 adapters."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from seedr_api.adapters.auto import AutoAdapter

_ASYNC_METHODS = [
    "login",
    "refresh_token",
    "get_device_code",
    "authorize_device",
    "get_settings",
    "get_memory_bandwidth",
    "get_devices",
    "list_contents",
    "get_folder",
    "get_file",
    "create_folder",
    "rename",
    "delete",
    "get_tasks",
    "get_task",
    "add_task",
    "delete_task",
    "get_file_url",
    "get_file_bytes",
    "init_archive",
    "search_files",
    "get_folder_presentations",
    "get_subtitles",
    "get_wishlist",
    "delete_wishlist_item",
    "get_torrent_progress",
    "close",
]


def _make_adapter() -> MagicMock:
    m = MagicMock()
    for method in _ASYNC_METHODS:
        setattr(m, method, AsyncMock(return_value="result"))
    return m


@pytest.fixture()
def v1() -> MagicMock:
    return _make_adapter()


@pytest.fixture()
def v2() -> MagicMock:
    return _make_adapter()


def test_no_adapters_raises() -> None:
    with pytest.raises(ValueError, match="At least one"):
        AutoAdapter()


def test_v2_only() -> None:
    v2 = _make_adapter()
    adapter = AutoAdapter(v2=v2)
    assert adapter.v2 is v2
    assert adapter.v1 is None


def test_v1_only() -> None:
    v1 = _make_adapter()
    adapter = AutoAdapter(v1=v1)
    assert adapter.v1 is v1
    assert adapter.v2 is None


def test_pick_prefers_v2(v1: MagicMock, v2: MagicMock) -> None:
    adapter = AutoAdapter(v1=v1, v2=v2, prefer_v2=True)
    assert adapter._pick() is v2


def test_pick_prefers_v1_when_prefer_v2_false(v1: MagicMock, v2: MagicMock) -> None:
    adapter = AutoAdapter(v1=v1, v2=v2, prefer_v2=False)
    assert adapter._pick() is v1


def test_pick_v2_only_returns_v2(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    assert adapter._pick() is v2


def test_pick_v1_only_returns_v1(v1: MagicMock) -> None:
    adapter = AutoAdapter(v1=v1)
    assert adapter._pick() is v1


def test_update_token_v2(v1: MagicMock, v2: MagicMock) -> None:
    adapter = AutoAdapter(v1=v1, v2=v2)
    adapter.update_token("new-tok", api_version="v2")
    v2.update_token.assert_called_once_with("new-tok")


def test_update_token_v1(v1: MagicMock, v2: MagicMock) -> None:
    adapter = AutoAdapter(v1=v1, v2=v2)
    adapter.update_token("new-tok", api_version="v1")
    v1.update_token.assert_called_once_with("new-tok")


async def test_login_without_v1_raises(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    with pytest.raises(RuntimeError, match="V1 adapter required"):
        await adapter.login("user", "pass")


async def test_login_with_v1(v1: MagicMock) -> None:
    adapter = AutoAdapter(v1=v1)
    await adapter.login("user", "pass")
    v1.login.assert_awaited_once_with("user", "pass")


async def test_refresh_token(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.refresh_token("ref", "cid")
    v2.refresh_token.assert_awaited_once_with("ref", "cid")


async def test_get_device_code(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.get_device_code("cid")
    v2.get_device_code.assert_awaited_once_with("cid")


async def test_authorize_device(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.authorize_device("dcode", "cid")
    v2.authorize_device.assert_awaited_once_with("dcode", "cid")


async def test_get_settings(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.get_settings()
    v2.get_settings.assert_awaited_once()


async def test_get_memory_bandwidth(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.get_memory_bandwidth()
    v2.get_memory_bandwidth.assert_awaited_once()


async def test_get_devices_with_v1(v1: MagicMock, v2: MagicMock) -> None:
    adapter = AutoAdapter(v1=v1, v2=v2)
    await adapter.get_devices()
    v1.get_devices.assert_awaited_once()


async def test_get_devices_without_v1(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    result = await adapter.get_devices()
    assert result == []


async def test_list_contents(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.list_contents(0)
    v2.list_contents.assert_awaited_once_with(0, "folder")


async def test_get_folder(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.get_folder(5)
    v2.get_folder.assert_awaited_once_with(5)


async def test_get_file(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.get_file(10)
    v2.get_file.assert_awaited_once_with(10)


async def test_create_folder(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.create_folder("test", 0)
    v2.create_folder.assert_awaited_once_with("test", 0)


async def test_rename(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.rename("new", folder_id=3)
    v2.rename.assert_awaited_once_with("new", folder_id=3, folder_file_id=None)


async def test_delete(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.delete([{"type": "folder", "id": 1}])
    v2.delete.assert_awaited_once()


async def test_get_tasks(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.get_tasks()
    v2.get_tasks.assert_awaited_once()


async def test_get_task(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.get_task(42)
    v2.get_task.assert_awaited_once_with(42)


async def test_add_task(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.add_task(torrent_magnet="magnet:?xt=abc")
    v2.add_task.assert_awaited_once_with(
        torrent_magnet="magnet:?xt=abc", wishlist_id=None, folder_id=None
    )


async def test_delete_task(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.delete_task(42)
    v2.delete_task.assert_awaited_once_with(42)


async def test_get_file_url(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.get_file_url(7)
    v2.get_file_url.assert_awaited_once_with(7)


async def test_get_file_bytes_prefers_v2(v1: MagicMock, v2: MagicMock) -> None:
    adapter = AutoAdapter(v1=v1, v2=v2)
    await adapter.get_file_bytes(7)
    v2.get_file_bytes.assert_awaited_once_with(7)
    v1.get_file_bytes.assert_not_awaited()


async def test_get_file_bytes_v1_only(v1: MagicMock) -> None:
    adapter = AutoAdapter(v1=v1)
    await adapter.get_file_bytes(7)
    v1.get_file_bytes.assert_awaited_once_with(7)


async def test_init_archive_prefers_v2(v1: MagicMock, v2: MagicMock) -> None:
    adapter = AutoAdapter(v1=v1, v2=v2)
    await adapter.init_archive("uuid", 0, [])
    v2.init_archive.assert_awaited_once_with("uuid", 0, [])
    v1.init_archive.assert_not_awaited()


async def test_init_archive_v1_only(v1: MagicMock) -> None:
    adapter = AutoAdapter(v1=v1)
    await adapter.init_archive("uuid", 0, [])
    v1.init_archive.assert_awaited_once_with("uuid", 0, [])


async def test_search_files(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.search_files("query")
    v2.search_files.assert_awaited_once_with("query")


async def test_scan_page_raises(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    with pytest.raises(NotImplementedError):
        await adapter.scan_page("http://example.com")


async def test_get_folder_presentations_v2(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.get_folder_presentations(1)
    v2.get_folder_presentations.assert_awaited_once_with(1)


async def test_get_folder_presentations_v1_only(v1: MagicMock) -> None:
    adapter = AutoAdapter(v1=v1)
    await adapter.get_folder_presentations(1)
    v1.get_folder_presentations.assert_awaited_once_with(1)


async def test_get_subtitles_v2(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.get_subtitles(5)
    v2.get_subtitles.assert_awaited_once_with(5)


async def test_get_subtitles_v1_only(v1: MagicMock) -> None:
    adapter = AutoAdapter(v1=v1)
    await adapter.get_subtitles(5)
    v1.get_subtitles.assert_awaited_once_with(5)


async def test_get_wishlist(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.get_wishlist()
    v2.get_wishlist.assert_awaited_once()


async def test_delete_wishlist_item(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    await adapter.delete_wishlist_item(3)
    v2.delete_wishlist_item.assert_awaited_once_with(3)


async def test_modify_account_name_raises(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    with pytest.raises(NotImplementedError):
        await adapter.modify_account_name("First", "Last")


async def test_modify_account_password_raises(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    with pytest.raises(NotImplementedError):
        await adapter.modify_account_password("old", "new")


async def test_get_torrent_progress_v1(v1: MagicMock) -> None:
    adapter = AutoAdapter(v1=v1)
    await adapter.get_torrent_progress("http://progress.url")
    v1.get_torrent_progress.assert_awaited_once_with("http://progress.url")


async def test_get_torrent_progress_v2_only_raises(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    with pytest.raises(NotImplementedError):
        await adapter.get_torrent_progress("http://progress.url")


async def test_create_archive_raises(v2: MagicMock) -> None:
    adapter = AutoAdapter(v2=v2)
    with pytest.raises(NotImplementedError):
        await adapter.create_archive([])


async def test_close_both(v1: MagicMock, v2: MagicMock) -> None:
    adapter = AutoAdapter(v1=v1, v2=v2)
    await adapter.close()
    v1.close.assert_awaited_once()
    v2.close.assert_awaited_once()
