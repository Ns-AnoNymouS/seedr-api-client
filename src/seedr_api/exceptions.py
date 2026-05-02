"""Full exception hierarchy for the seedr-api library."""

from __future__ import annotations

from typing import Any


class SeedrError(Exception):
    """Base exception for all Seedr API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(status_code={self.status_code}, message={self.message!r})"


class AuthenticationError(SeedrError):
    """Raised when the request is not authenticated (HTTP 401)."""


class TokenExpiredError(AuthenticationError):
    """Raised when the OAuth access token has expired (before refresh attempt)."""


class ForbiddenError(SeedrError):
    """Raised when the authenticated user lacks permission (HTTP 403)."""


class NotFoundError(SeedrError):
    """Raised when a requested resource does not exist (HTTP 404)."""


class RateLimitError(SeedrError):
    """Raised when the API rate limit is exceeded (HTTP 429)."""

    def __init__(
        self,
        message: str,
        status_code: int | None = 429,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message, status_code)
        self.retry_after = retry_after


class InsufficientSpaceError(SeedrError):
    """Raised when adding a task fails because the user is out of space (HTTP 413).

    The torrent is automatically added to the wishlist by the API.
    ``wishlist_item`` contains the raw wishlist entry dict returned by the API.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = 413,
        wishlist_item: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code)
        self.wishlist_item = wishlist_item


class ServerError(SeedrError):
    """Raised for server-side errors (HTTP 5xx)."""


class APIError(SeedrError):
    """Raised for unexpected HTTP errors not covered by other exceptions."""
