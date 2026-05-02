"""seedr_api — Async Python client for the Seedr API.

Public API::

    from seedr_api import SeedrClient, SeedrClientBuilder, SeedrSession
    from seedr_api.exceptions import SeedrError, AuthenticationError

Quickstart::

    # V2 OAuth token
    async with SeedrClient.from_token("your-access-token") as client:
        root = await client.filesystem.list_root_contents()

    # Username / password (V1 API)
    client = await SeedrClient.from_credentials("you@example.com", "secret")
    async with client:
        settings = await client.account.get_settings()

    # Fluent builder
    from seedr_api.core.token_storage import FileTokenStorage
    client = (
        SeedrClientBuilder()
        .with_v2_token("access-token")
        .with_refresh_token("refresh-token", client_id="seedr_chrome")
        .with_token_storage(FileTokenStorage(".token.json"))
        .build()
    )

    # Long-lived session
    from seedr_api import SeedrSession
    session = await SeedrSession.create("user@example.com", "pass")
"""

from __future__ import annotations

from seedr_api.builder import SeedrClientBuilder
from seedr_api.client import SeedrClient
from seedr_api.exceptions import (
    APIError,
    AuthenticationError,
    ForbiddenError,
    InsufficientSpaceError,
    NotFoundError,
    RateLimitError,
    SeedrError,
    ServerError,
    TokenExpiredError,
)
from seedr_api.session import SeedrSession

try:
    from seedr_api._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "APIError",
    "AuthenticationError",
    "ForbiddenError",
    "InsufficientSpaceError",
    "NotFoundError",
    "RateLimitError",
    "SeedrClient",
    "SeedrClientBuilder",
    "SeedrError",
    "SeedrSession",
    "ServerError",
    "TokenExpiredError",
    "__version__",
]
