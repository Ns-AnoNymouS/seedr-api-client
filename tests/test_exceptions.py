"""Tests for the exception hierarchy and HTTP error mapping via V2 adapter."""

from __future__ import annotations

import pytest
from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from seedr_api.exceptions import (
    APIError,
    AuthenticationError,
    ForbiddenError,
    InsufficientSpaceError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TokenExpiredError,
)
from tests.conftest import API_BASE


@pytest.mark.parametrize(
    ("status", "exc_type"),
    [
        (401, AuthenticationError),
        (403, ForbiddenError),
        (404, NotFoundError),
        (429, RateLimitError),
        (500, ServerError),
        (422, APIError),
    ],
)
async def test_http_error_mapping(
    mock_aioresponses: aioresponses,
    token_client: SeedrClient,
    status: int,
    exc_type: type,
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/me/settings",
        status=status,
        payload={"status_code": status, "reason_phrase": "err"},
    )
    async with token_client:
        with pytest.raises(exc_type):
            await token_client.account.get_settings()


async def test_rate_limit_has_retry_after(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/me/settings",
        status=429,
        headers={"Retry-After": "30"},
        payload={"reason_phrase": "Too many requests"},
    )
    async with token_client:
        with pytest.raises(RateLimitError) as exc_info:
            await token_client.account.get_settings()
    assert exc_info.value.retry_after == 30


async def test_413_raises_insufficient_space_with_wishlist(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    wt = {"id": 1, "title": "Big Movie", "torrent_hash": "abc"}
    mock_aioresponses.post(
        f"{API_BASE}/tasks",
        status=413,
        payload={"reason_phrase": "not_enough_space_added_to_wishlist", "wt": wt},
    )
    async with token_client:
        with pytest.raises(InsufficientSpaceError) as exc_info:
            await token_client.tasks.add_magnet("magnet:?xt=abc")
    assert exc_info.value.wishlist_item == wt
    assert exc_info.value.status_code == 413


async def test_token_expired_is_authentication_error() -> None:
    err = TokenExpiredError("Token expired", status_code=401)
    assert isinstance(err, AuthenticationError)
    assert err.status_code == 401


def test_exception_hierarchy() -> None:
    # All specific errors inherit from SeedrError
    from seedr_api.exceptions import SeedrError

    assert issubclass(AuthenticationError, SeedrError)
    assert issubclass(TokenExpiredError, AuthenticationError)
    assert issubclass(ForbiddenError, SeedrError)
    assert issubclass(NotFoundError, SeedrError)
    assert issubclass(RateLimitError, SeedrError)
    assert issubclass(InsufficientSpaceError, SeedrError)
    assert issubclass(ServerError, SeedrError)
    assert issubclass(APIError, SeedrError)
