"""SeedrClientBuilder — fluent builder for constructing SeedrClient instances.

Example::

    from seedr_api import SeedrClientBuilder
    from seedr_api.core.token_storage import FileTokenStorage

    client = (
        SeedrClientBuilder()
        .with_v2_token("my-access-token")
        .with_refresh_token("my-refresh-token", client_id="seedr_chrome")
        .on_token_refresh(save_my_tokens)
        .with_timeout(120.0)
        .build()
    )
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from seedr_api.client import SeedrClient
from seedr_api.core.token import Token

if TYPE_CHECKING:
    from seedr_api.core.token_storage import TokenStorageProtocol


class SeedrClientBuilder:
    """Fluent builder for creating :class:`SeedrClient` instances.

    Call the ``with_*`` / ``on_*`` methods to configure the client,
    then call :meth:`build` to get the client instance.
    """

    def __init__(self) -> None:
        self._v1_token: str | None = None
        self._v2_token: str | None = None
        self._v1_refresh_token: str | None = None
        self._v2_refresh_token: str | None = None
        self._client_id: str | None = None
        self._timeout: float = 60.0
        self._storage: TokenStorageProtocol | None = None
        self._on_token_refresh: Callable[[Token], Awaitable[None]] | None = None
        self._prefer_v2: bool = True

    # ------------------------------------------------------------------
    # Token configuration
    # ------------------------------------------------------------------

    def with_v2_token(self, access_token: str) -> SeedrClientBuilder:
        """Set the V2 OAuth access token.

        Parameters
        ----------
        access_token:
            V2 OAuth access token.
        """
        self._v2_token = access_token
        return self

    def with_v1_token(self, access_token: str) -> SeedrClientBuilder:
        """Set the V1 access token.

        Parameters
        ----------
        access_token:
            V1 access token.
        """
        self._v1_token = access_token
        return self

    def with_refresh_token(
        self,
        refresh_token: str,
        *,
        client_id: str | None = None,
    ) -> SeedrClientBuilder:
        """Set the refresh token (applies to whichever API version is active).

        Parameters
        ----------
        refresh_token:
            OAuth refresh token.
        client_id:
            OAuth client ID. Required for auto-refresh.
        """
        if self._v2_token is not None:
            self._v2_refresh_token = refresh_token
        else:
            self._v1_refresh_token = refresh_token
        if client_id is not None:
            self._client_id = client_id
        return self

    def with_v1_refresh_token(
        self,
        refresh_token: str,
        *,
        client_id: str | None = None,
    ) -> SeedrClientBuilder:
        """Set the V1 refresh token explicitly.

        Parameters
        ----------
        refresh_token:
            V1 refresh token.
        client_id:
            OAuth client ID.
        """
        self._v1_refresh_token = refresh_token
        if client_id is not None:
            self._client_id = client_id
        return self

    def with_v2_refresh_token(
        self,
        refresh_token: str,
        *,
        client_id: str | None = None,
    ) -> SeedrClientBuilder:
        """Set the V2 refresh token explicitly.

        Parameters
        ----------
        refresh_token:
            V2 refresh token.
        client_id:
            OAuth client ID.
        """
        self._v2_refresh_token = refresh_token
        if client_id is not None:
            self._client_id = client_id
        return self

    def with_client_id(self, client_id: str) -> SeedrClientBuilder:
        """Set the OAuth client ID.

        Parameters
        ----------
        client_id:
            OAuth client ID (e.g. ``seedr_chrome``).
        """
        self._client_id = client_id
        return self

    # ------------------------------------------------------------------
    # Behaviour configuration
    # ------------------------------------------------------------------

    def with_timeout(self, timeout: float) -> SeedrClientBuilder:
        """Set the request timeout.

        Parameters
        ----------
        timeout:
            Total request timeout in seconds.
        """
        self._timeout = timeout
        return self

    def with_token_storage(
        self, storage: TokenStorageProtocol
    ) -> SeedrClientBuilder:
        """Set the token storage backend.

        Tokens will be persisted after each refresh.

        Parameters
        ----------
        storage:
            A :class:`~seedr_api.core.token_storage.TokenStorageProtocol`
            implementation.
        """
        self._storage = storage
        return self

    def on_token_refresh(
        self, callback: Callable[[Token], Awaitable[None]]
    ) -> SeedrClientBuilder:
        """Register a callback invoked after every token refresh.

        Parameters
        ----------
        callback:
            Async callable that receives the new :class:`Token`.
        """
        self._on_token_refresh = callback
        return self

    def prefer_v1(self) -> SeedrClientBuilder:
        """Prefer the V1 adapter when both V1 and V2 tokens are provided."""
        self._prefer_v2 = False
        return self

    def prefer_v2(self) -> SeedrClientBuilder:
        """Prefer the V2 adapter when both V1 and V2 tokens are provided (default)."""
        self._prefer_v2 = True
        return self

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> SeedrClient:
        """Construct and return the :class:`SeedrClient`.

        Returns
        -------
        SeedrClient

        Raises
        ------
        ValueError
            If no token has been configured.
        """
        if self._v1_token is None and self._v2_token is None:
            raise ValueError(
                "At least one token must be provided. "
                "Call with_v2_token() or with_v1_token() first."
            )

        # Wrap storage into on_token_refresh if provided
        effective_callback = self._on_token_refresh
        if self._storage is not None:
            storage = self._storage

            async def _storage_callback(token: Token) -> None:
                await storage.save(token)
                if self._on_token_refresh is not None:
                    await self._on_token_refresh(token)

            effective_callback = _storage_callback

        if self._v1_token is not None and self._v2_token is not None:
            # Both tokens — build AutoAdapter
            return SeedrClient.from_tokens(
                v1_token=self._v1_token,
                v2_token=self._v2_token,
                v1_refresh_token=self._v1_refresh_token,
                v2_refresh_token=self._v2_refresh_token,
                client_id=self._client_id,
                on_token_refresh=effective_callback,
                timeout=self._timeout,
            )

        if self._v2_token is not None:
            return SeedrClient.from_token(
                self._v2_token,
                refresh_token=self._v2_refresh_token,
                client_id=self._client_id,
                on_token_refresh=effective_callback,
                timeout=self._timeout,
            )

        # V1 only
        assert self._v1_token is not None
        return SeedrClient.from_v1_token(
            self._v1_token,
            refresh_token=self._v1_refresh_token,
            client_id=self._client_id,
            on_token_refresh=effective_callback,
            timeout=self._timeout,
        )

    def __repr__(self) -> str:
        has_v2 = bool(self._v2_token)
        has_v1 = bool(self._v1_token)
        has_refresh = bool(self._v1_refresh_token or self._v2_refresh_token)
        return (
            f"SeedrClientBuilder("
            f"v2={has_v2}, v1={has_v1}, "
            f"refresh={has_refresh}, "
            f"storage={self._storage is not None})"
        )
