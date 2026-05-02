"""Shared pytest fixtures for seedr-api tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from aioresponses import aioresponses

from seedr_api.client import SeedrClient

# The V2 adapter uses this base URL
API_BASE = "https://v2.seedr.cc/api/v0.1/p"
DEVICE_CODE_URL = f"{API_BASE}/oauth/device/code"
DEVICE_TOKEN_URL = f"{API_BASE}/oauth/device/token"


@pytest.fixture()
def mock_aioresponses() -> Generator[aioresponses, None, None]:
    """Provide an aioresponses context for mocking aiohttp."""
    with aioresponses() as m:
        yield m


@pytest.fixture()
def token_client() -> SeedrClient:
    """Return a SeedrClient authenticated with a fake V2 OAuth token."""
    return SeedrClient.from_token("fake-access-token")
