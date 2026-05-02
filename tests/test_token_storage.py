"""Tests for MemoryTokenStorage and FileTokenStorage."""

from __future__ import annotations

from pathlib import Path

from seedr_api.core.token import Token
from seedr_api.core.token_storage import FileTokenStorage, MemoryTokenStorage


async def test_memory_storage_empty() -> None:
    storage = MemoryTokenStorage()
    assert await storage.load() is None


async def test_memory_storage_save_and_load() -> None:
    storage = MemoryTokenStorage()
    t = Token(access_token="abc", refresh_token="ref")
    await storage.save(t)
    loaded = await storage.load()
    assert loaded is t


async def test_memory_storage_delete() -> None:
    storage = MemoryTokenStorage()
    t = Token(access_token="abc")
    await storage.save(t)
    await storage.delete()
    assert await storage.load() is None


async def test_file_storage_load_missing_file(tmp_path: Path) -> None:
    storage = FileTokenStorage(tmp_path / "token.json")
    assert await storage.load() is None


async def test_file_storage_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "token.json"
    storage = FileTokenStorage(path)
    t = Token(access_token="tok", refresh_token="ref", client_id="c")
    await storage.save(t)
    assert path.exists()
    loaded = await storage.load()
    assert loaded is not None
    assert loaded.access_token == "tok"
    assert loaded.refresh_token == "ref"
    assert loaded.client_id == "c"


async def test_file_storage_delete(tmp_path: Path) -> None:
    path = tmp_path / "token.json"
    storage = FileTokenStorage(path)
    await storage.save(Token(access_token="tok"))
    assert path.exists()
    await storage.delete()
    assert not path.exists()


async def test_file_storage_delete_nonexistent(tmp_path: Path) -> None:
    storage = FileTokenStorage(tmp_path / "missing.json")
    await storage.delete()  # should not raise


async def test_file_storage_bad_json(tmp_path: Path) -> None:
    path = tmp_path / "token.json"
    path.write_text("not valid json")
    storage = FileTokenStorage(path)
    assert await storage.load() is None


async def test_file_storage_creates_parent_dirs(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "deep" / "token.json"
    storage = FileTokenStorage(path)
    await storage.save(Token(access_token="tok"))
    assert path.exists()
