"""Tests for the exception hierarchy and _http error mapping."""

import pytest
from aioresponses import aioresponses

from seedr_api.client import SeedrClient
from seedr_api.exceptions import (
    APIError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
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
    mock_aioresponses.get(f"{API_BASE}/user", status=status, payload={"error": "err"})
    async with token_client:
        with pytest.raises(exc_type):
            await token_client.user.get()


async def test_rate_limit_has_retry_after(
    mock_aioresponses: aioresponses, token_client: SeedrClient
) -> None:
    mock_aioresponses.get(
        f"{API_BASE}/user",
        status=429,
        headers={"Retry-After": "30"},
        payload={"error": "Too many requests"},
    )
    async with token_client:
        with pytest.raises(RateLimitError) as exc_info:
            await token_client.user.get()
    assert exc_info.value.retry_after == 30
