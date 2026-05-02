"""Tests for Token dataclass and TokenManager."""

from __future__ import annotations

import time

import pytest

from seedr_api.core.token import Token, TokenManager
from seedr_api.core.token_storage import MemoryTokenStorage


def test_token_defaults() -> None:
    t = Token(access_token="abc")
    assert t.access_token == "abc"
    assert t.refresh_token is None
    assert t.expires_at is None
    assert not t.is_expired()


def test_token_from_response_with_expires_in() -> None:
    t = Token.from_response(
        "tok", refresh_token="ref", expires_in=3600, client_id="cid"
    )
    assert t.access_token == "tok"
    assert t.refresh_token == "ref"
    assert t.client_id == "cid"
    assert t.expires_at is not None
    assert t.expires_at > time.time()
    assert not t.is_expired()


def test_token_from_response_no_expires() -> None:
    t = Token.from_response("tok")
    assert t.expires_at is None
    assert not t.is_expired()


def test_token_is_expired_true() -> None:
    t = Token(access_token="tok", expires_at=time.time() - 10)
    assert t.is_expired()


def test_token_to_dict() -> None:
    t = Token(access_token="a", refresh_token="r", expires_at=1.0, client_id="c")
    d = t.to_dict()
    assert d["access_token"] == "a"
    assert d["refresh_token"] == "r"
    assert d["expires_at"] == 1.0
    assert d["client_id"] == "c"


def test_token_from_dict_roundtrip() -> None:
    data = {
        "access_token": "a",
        "refresh_token": "r",
        "expires_at": 1.0,
        "client_id": "c",
        "custom_key": "x",
    }
    t = Token.from_dict(data)
    assert t.access_token == "a"
    assert t.refresh_token == "r"
    assert t.expires_at == 1.0
    assert t.client_id == "c"
    assert t.extra == {"custom_key": "x"}


async def test_token_manager_no_refresh_fn() -> None:
    t = Token(access_token="tok", refresh_token="ref")
    mgr = TokenManager(t)
    assert mgr.token is t
    assert not mgr.can_refresh()


async def test_token_manager_can_refresh() -> None:
    t = Token(access_token="tok", refresh_token="ref")
    new_t = Token(access_token="new")

    async def refresh_fn(rt: str) -> Token:
        return new_t

    mgr = TokenManager(t, refresh_fn=refresh_fn)
    assert mgr.can_refresh()
    result = await mgr.refresh()
    assert result is new_t
    assert mgr.token is new_t


async def test_token_manager_refresh_raises_without_fn() -> None:
    t = Token(access_token="tok", refresh_token="ref")
    mgr = TokenManager(t)
    with pytest.raises(RuntimeError, match="No refresh function"):
        await mgr.refresh()


async def test_token_manager_refresh_saves_to_storage_and_calls_callback() -> None:
    t = Token(access_token="tok", refresh_token="ref")
    new_t = Token(access_token="new")
    callbacks: list[Token] = []

    async def refresh_fn(rt: str) -> Token:
        return new_t

    storage = MemoryTokenStorage()

    async def on_refresh(token: Token) -> None:
        callbacks.append(token)

    mgr = TokenManager(
        t, refresh_fn=refresh_fn, storage=storage, on_token_refresh=on_refresh
    )
    await mgr.refresh()

    assert await storage.load() is new_t
    assert callbacks == [new_t]


async def test_token_manager_get_valid_token_not_expired() -> None:
    t = Token(access_token="tok", expires_at=time.time() + 3600)
    mgr = TokenManager(t)
    result = await mgr.get_valid_token()
    assert result is t


async def test_token_manager_get_valid_token_expired_refreshes() -> None:
    t = Token(access_token="old", refresh_token="ref", expires_at=time.time() - 10)
    new_t = Token(access_token="new")

    async def refresh_fn(rt: str) -> Token:
        return new_t

    mgr = TokenManager(t, refresh_fn=refresh_fn)
    result = await mgr.get_valid_token()
    assert result is new_t
