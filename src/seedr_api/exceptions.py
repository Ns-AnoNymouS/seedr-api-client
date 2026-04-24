"""Custom exceptions for the seedr-api library."""

from __future__ import annotations


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


class ServerError(SeedrError):
    """Raised for server-side errors (HTTP 5xx)."""


class APIError(SeedrError):
    """Raised for unexpected HTTP 4xx errors not covered by other exceptions."""
