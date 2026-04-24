"""Fixtures for integration tests — uses the real Seedr API."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from seedr_api.client import SeedrClient

_TOKEN_FILE = Path(__file__).parent.parent.parent / ".token"

#: Default public client ID used for device-code / PKCE tests.
SEEDR_CLIENT_ID = os.getenv("SEEDR_CLIENT_ID", "V94K2IfOGY2BNYTrJTFeTtJ1VOuKzM52")
#: Optional client secret — required only for client-credentials flow.
SEEDR_CLIENT_SECRET = os.getenv("SEEDR_CLIENT_SECRET")


def _get_token() -> str:
    token = os.getenv("SEEDR_TOKEN")
    if token:
        return token.strip()
    if _TOKEN_FILE.exists():
        return _TOKEN_FILE.read_text().strip()
    pytest.skip("No SEEDR_TOKEN env var or .token file found")


@pytest.fixture()
def token() -> str:
    """Raw Bearer token string, for tests that need it directly."""
    return _get_token()


@pytest.fixture()
async def client() -> AsyncIterator[SeedrClient]:
    """Authenticated SeedrClient for each integration test."""
    async with SeedrClient.from_token(_get_token()) as c:
        yield c
