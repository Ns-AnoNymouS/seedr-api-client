"""SeedrSession — long-lived session with token persistence.

Typical usage::

    session = await SeedrSession.create("user@example.com", "pass")
    async with session.client as client:
        root = await client.filesystem.list_root_contents()
    await session.save()

Or with FileTokenStorage::

    storage = FileTokenStorage(".token.json")
    session = await SeedrSession.load_or_create(
        storage,
        username="user@example.com",
        password="pass",
    )
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from seedr_api.client import SeedrClient
from seedr_api.core.token import Token
from seedr_api.core.token_storage import (
    MemoryTokenStorage,
    TokenStorageProtocol,
)

if TYPE_CHECKING:
    pass


class SeedrSession:
    """Long-lived session that persists OAuth tokens across process restarts.

    Parameters
    ----------
    client:
        The underlying :class:`SeedrClient`.
    token:
        Current :class:`Token`.
    storage:
        Storage backend used to persist/load tokens.
    """

    def __init__(
        self,
        client: SeedrClient,
        token: Token,
        storage: TokenStorageProtocol,
    ) -> None:
        self._client = client
        self._token = token
        self._storage = storage

    @property
    def client(self) -> SeedrClient:
        """The underlying :class:`SeedrClient`."""
        return self._client

    @property
    def token(self) -> Token:
        """The current token."""
        return self._token

    @classmethod
    async def create(
        cls,
        username: str,
        password: str,
        *,
        client_id: str = "seedr_chrome",
        storage: TokenStorageProtocol | None = None,
        on_token_refresh: Callable[[Token], Awaitable[None]] | None = None,
        timeout: float = 60.0,
    ) -> SeedrSession:
        """Create a new session by logging in with username and password.

        Parameters
        ----------
        username:
            Seedr account username or email.
        password:
            Seedr account password.
        client_id:
            OAuth client ID.
        storage:
            Optional storage backend. Defaults to :class:`MemoryTokenStorage`.
        on_token_refresh:
            Async callback called after each token refresh.
        timeout:
            Request timeout in seconds.

        Returns
        -------
        SeedrSession
        """

        _storage = storage or MemoryTokenStorage()

        # Build a save-on-refresh callback that also calls the user's callback
        async def _refresh_callback(new_token: Token) -> None:
            await _storage.save(new_token)
            if on_token_refresh is not None:
                await on_token_refresh(new_token)

        client = await SeedrClient.from_credentials(
            username,
            password,
            client_id=client_id,
            on_token_refresh=_refresh_callback,
            timeout=timeout,
        )

        # Build initial token object
        access_token = client.access_token
        token = Token(access_token=access_token, client_id=client_id)
        await _storage.save(token)

        return cls(client, token, _storage)

    @classmethod
    async def from_token(
        cls,
        token: Token,
        *,
        storage: TokenStorageProtocol | None = None,
        on_token_refresh: Callable[[Token], Awaitable[None]] | None = None,
        timeout: float = 60.0,
    ) -> SeedrSession:
        """Create a session from an existing :class:`Token`.

        Parameters
        ----------
        token:
            An existing token (loaded from storage or obtained externally).
        storage:
            Optional storage backend.
        on_token_refresh:
            Async callback called after each token refresh.
        timeout:
            Request timeout in seconds.

        Returns
        -------
        SeedrSession
        """
        _storage = storage or MemoryTokenStorage()

        async def _refresh_callback(new_token: Token) -> None:
            await _storage.save(new_token)
            if on_token_refresh is not None:
                await on_token_refresh(new_token)

        client = SeedrClient.from_v1_token(
            token.access_token,
            refresh_token=token.refresh_token,
            client_id=token.client_id or "seedr_chrome",
            on_token_refresh=_refresh_callback,
            timeout=timeout,
        )

        return cls(client, token, _storage)

    @classmethod
    async def load_or_create(
        cls,
        storage: TokenStorageProtocol,
        *,
        username: str,
        password: str,
        client_id: str = "seedr_chrome",
        on_token_refresh: Callable[[Token], Awaitable[None]] | None = None,
        timeout: float = 60.0,
    ) -> SeedrSession:
        """Load a persisted session or create a new one if none is found.

        Parameters
        ----------
        storage:
            Storage backend to load from and save to.
        username:
            Seedr account username (used if no saved token is found).
        password:
            Seedr account password (used if no saved token is found).
        client_id:
            OAuth client ID.
        on_token_refresh:
            Async callback called after each token refresh.
        timeout:
            Request timeout in seconds.

        Returns
        -------
        SeedrSession
        """
        existing = await storage.load()
        if existing is not None:
            return await cls.from_token(
                existing,
                storage=storage,
                on_token_refresh=on_token_refresh,
                timeout=timeout,
            )
        return await cls.create(
            username,
            password,
            client_id=client_id,
            storage=storage,
            on_token_refresh=on_token_refresh,
            timeout=timeout,
        )

    async def save(self) -> None:
        """Persist the current token to storage."""
        await self._storage.save(self._token)

    async def close(self) -> None:
        """Close the session client."""
        await self._client.close()

    async def __aenter__(self) -> SeedrSession:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    def __repr__(self) -> str:
        return f"SeedrSession(client={self._client!r})"
