"""Token dataclass and TokenManager for auto-refresh logic."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from seedr_api.core.token_storage import TokenStorageProtocol


@dataclass
class Token:
    """Represents an OAuth token pair with optional expiry tracking.

    Parameters
    ----------
    access_token:
        The OAuth access token.
    refresh_token:
        The OAuth refresh token (may be None for client-credentials tokens).
    expires_at:
        UNIX timestamp when the access token expires. None means unknown.
    client_id:
        OAuth client ID used to refresh this token.
    """

    access_token: str
    refresh_token: str | None = None
    expires_at: float | None = None
    client_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_response(
        cls,
        access_token: str,
        *,
        refresh_token: str | None = None,
        expires_in: int | None = None,
        client_id: str | None = None,
        **extra: Any,
    ) -> Token:
        """Construct a Token from raw API response fields."""
        expires_at: float | None = None
        if expires_in is not None:
            expires_at = time.time() + expires_in - 30  # 30-second buffer
        return cls(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            client_id=client_id,
            extra=extra,
        )

    def is_expired(self) -> bool:
        """Return True if the token has definitely expired."""
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict for storage."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "client_id": self.client_id,
            **self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Token:
        """Deserialize from a plain dict (e.g. from storage)."""
        extra = {
            k: v
            for k, v in data.items()
            if k not in ("access_token", "refresh_token", "expires_at", "client_id")
        }
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=data.get("expires_at"),
            client_id=data.get("client_id"),
            extra=extra,
        )


class TokenManager:
    """Manages token refresh with optional storage persistence.

    Wraps a callable that performs the actual token refresh.  After a
    successful refresh the new token is saved to the optional storage
    backend and the ``on_token_refresh`` callback is invoked.

    Parameters
    ----------
    token:
        Initial :class:`Token` instance.
    refresh_fn:
        Async callable that accepts the current refresh token and returns
        a new :class:`Token`.
    storage:
        Optional storage backend.  When provided the token is persisted
        after every refresh.
    on_token_refresh:
        Optional async callback invoked after a successful refresh with
        the new token.
    """

    def __init__(
        self,
        token: Token,
        *,
        refresh_fn: Callable[[str], Awaitable[Token]] | None = None,
        storage: TokenStorageProtocol | None = None,
        on_token_refresh: Callable[[Token], Awaitable[None]] | None = None,
    ) -> None:
        self._token = token
        self._refresh_fn = refresh_fn
        self._storage = storage
        self._on_token_refresh = on_token_refresh

    @property
    def token(self) -> Token:
        """The current token."""
        return self._token

    def can_refresh(self) -> bool:
        """Return True if a refresh is possible."""
        return self._refresh_fn is not None and self._token.refresh_token is not None

    async def refresh(self) -> Token:
        """Perform a token refresh and return the new token.

        Raises
        ------
        RuntimeError
            If no refresh function or refresh token is available.
        """
        if not self.can_refresh():
            raise RuntimeError("No refresh function or refresh token available.")

        assert self._refresh_fn is not None
        assert self._token.refresh_token is not None

        new_token = await self._refresh_fn(self._token.refresh_token)
        self._token = new_token

        if self._storage is not None:
            await self._storage.save(new_token)
        if self._on_token_refresh is not None:
            await self._on_token_refresh(new_token)

        return new_token

    async def get_valid_token(self) -> Token:
        """Return a valid (non-expired) token, refreshing if necessary."""
        if self._token.is_expired() and self.can_refresh():
            return await self.refresh()
        return self._token
