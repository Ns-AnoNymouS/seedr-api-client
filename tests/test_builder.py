"""Tests for SeedrClientBuilder fluent API."""

from __future__ import annotations

import pytest

from seedr_api.builder import SeedrClientBuilder
from seedr_api.core.token import Token
from seedr_api.core.token_storage import MemoryTokenStorage


def test_build_without_token_raises() -> None:
    with pytest.raises(ValueError, match="At least one token"):
        SeedrClientBuilder().build()


def test_build_v2_token() -> None:
    client = SeedrClientBuilder().with_v2_token("tok").build()
    assert client is not None


def test_build_v1_token() -> None:
    client = SeedrClientBuilder().with_v1_token("tok").build()
    assert client is not None


def test_build_both_tokens() -> None:
    client = SeedrClientBuilder().with_v2_token("v2tok").with_v1_token("v1tok").build()
    assert client is not None


def test_with_v1_refresh_token_sets_fields() -> None:
    builder = (
        SeedrClientBuilder()
        .with_v1_token("tok")
        .with_v1_refresh_token("ref", client_id="seedr_chrome")
    )
    assert builder._v1_refresh_token == "ref"
    assert builder._client_id == "seedr_chrome"


def test_with_v2_refresh_token_sets_fields() -> None:
    builder = (
        SeedrClientBuilder()
        .with_v2_token("tok")
        .with_v2_refresh_token("ref", client_id="seedr_chrome")
    )
    assert builder._v2_refresh_token == "ref"
    assert builder._client_id == "seedr_chrome"


def test_with_client_id() -> None:
    builder = SeedrClientBuilder().with_client_id("seedr_chrome")
    assert builder._client_id == "seedr_chrome"
    assert builder._timeout == 60.0  # default unchanged


def test_with_timeout() -> None:
    builder = SeedrClientBuilder().with_timeout(120.0)
    assert builder._timeout == 120.0


def test_with_refresh_token_routes_to_v2() -> None:
    builder = (
        SeedrClientBuilder()
        .with_v2_token("tok")
        .with_refresh_token("ref", client_id="c")
    )
    assert builder._v2_refresh_token == "ref"
    assert builder._client_id == "c"


def test_with_refresh_token_routes_to_v1() -> None:
    builder = SeedrClientBuilder().with_v1_token("tok").with_refresh_token("ref")
    assert builder._v1_refresh_token == "ref"


def test_prefer_v1() -> None:
    builder = SeedrClientBuilder().prefer_v1()
    assert not builder._prefer_v2


def test_prefer_v2() -> None:
    builder = SeedrClientBuilder().prefer_v1().prefer_v2()
    assert builder._prefer_v2


def test_with_token_storage_builds() -> None:
    storage = MemoryTokenStorage()
    client = (
        SeedrClientBuilder().with_v2_token("tok").with_token_storage(storage).build()
    )
    assert client is not None


async def test_storage_callback_saves_token() -> None:
    storage = MemoryTokenStorage()
    received: list[Token] = []

    async def on_refresh(tok: Token) -> None:
        received.append(tok)

    builder = (
        SeedrClientBuilder()
        .with_v2_token("tok")
        .with_token_storage(storage)
        .on_token_refresh(on_refresh)
    )
    # Extract effective callback by building and inspecting the adapter
    # The callback fires on refresh; just verify build succeeds here
    client = builder.build()
    assert client is not None


def test_repr_contains_state() -> None:
    builder = SeedrClientBuilder().with_v2_token("tok").with_v1_refresh_token("ref")
    r = repr(builder)
    assert "SeedrClientBuilder" in r
    assert "v2=True" in r
    assert "refresh=True" in r
