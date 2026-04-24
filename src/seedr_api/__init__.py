"""seedr — Async Python client for the Seedr API.

Public API::

    from seedr_api import SeedrClient
    from seedr_api.exceptions import SeedrError, AuthenticationError, NotFoundError

Example::

    async with SeedrClient.from_token("your-token") as client:
        root = await client.filesystem.list_root_contents()
        task = await client.tasks.add_magnet("magnet:?xt=...")
"""

from __future__ import annotations

from seedr_api.client import SeedrClient
from seedr_api.exceptions import (
    APIError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    SeedrError,
    ServerError,
)

try:
    from seedr_api._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "APIError",
    "AuthenticationError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "SeedrClient",
    "SeedrError",
    "ServerError",
    "__version__",
]
