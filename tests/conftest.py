"""Shared pytest fixtures for seedr-api tests."""

from collections.abc import Generator

import pytest
from aioresponses import aioresponses

from seedr_api.client import SeedrClient

OAUTH_BASE = "https://www.seedr.cc/api/v0.1"
PASSWORD_BASE = "https://www.seedr.cc/api/v0.1/p"


@pytest.fixture()
def mock_aioresponses() -> Generator[aioresponses, None, None]:
    """Provide an aioresponses context for mocking aiohttp."""
    with aioresponses() as m:
        yield m


@pytest.fixture()
def token_client() -> SeedrClient:
    """Return a SeedrClient authenticated with a fake OAuth token."""
    return SeedrClient.from_token("fake-access-token")


@pytest.fixture()
def credentials_client() -> SeedrClient:
    """Return a SeedrClient authenticated with email/password."""
    return SeedrClient.from_credentials("user@example.com", "password123")
