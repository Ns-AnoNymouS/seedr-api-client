"""SeedrClient — main entry point for the seedr-api library.

Supports all 10 usage patterns:

1. V2 OAuth token (most common):
    async with SeedrClient.from_token("access_token") as client: ...

2. V2 OAuth token + auto-refresh:
    async with SeedrClient.from_token(
        "access_token",
        refresh_token="rt",
        client_id="seedr_chrome",
        on_token_refresh=save_tokens,
    ) as client: ...

3. V1 username/password (obtains token automatically):
    client = await SeedrClient.from_credentials("user@example.com", "pass")

4. V1 adapter only (existing token):
    client = SeedrClient.from_v1_token("access_token")

5. Auto adapter (V1 + V2 both available):
    client = SeedrClient.from_tokens(v1_token="t1", v2_token="t2")

6. Builder pattern:
    client = (
        SeedrClientBuilder()
        .with_v2_token("access_token")
        .with_refresh_token("rt", client_id="seedr_chrome")
        .on_token_refresh(save_tokens)
        .build()
    )

7. File token storage:
    client = (
        SeedrClientBuilder()
        .with_v2_token("access_token")
        .with_token_storage(FileTokenStorage(".token.json"))
        .build()
    )

8. Session pattern (long-lived):
    session = await SeedrSession.create("user@example.com", "pass")
    client = session.client

9. Custom timeout:
    client = SeedrClient.from_token("access_token", timeout=120.0)

10. Anonymous (no auth, for device code flow):
    client = SeedrClient.anonymous()
    dc = await client.auth.request_device_code("seedr_xbmc")
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from seedr_api.adapters.v1 import V1Adapter
from seedr_api.adapters.v2 import V2Adapter
from seedr_api.core.token import Token
from seedr_api.exceptions import AuthenticationError, TokenExpiredError
from seedr_api.resources.account import AccountResource
from seedr_api.resources.auth import AuthResource
from seedr_api.resources.downloads import DownloadsResource
from seedr_api.resources.filesystem import FilesystemResource
from seedr_api.resources.presentations import PresentationsResource
from seedr_api.resources.search import SearchResource
from seedr_api.resources.subtitles import SubtitlesResource
from seedr_api.resources.tasks import TasksResource

if TYPE_CHECKING:
    pass

# Any adapter type
_AnyAdapter = Any  # V1Adapter | V2Adapter | AutoAdapter


class SeedrClient:
    """Async client for the Seedr API.

    Prefer the class-method constructors over direct instantiation.

    Parameters
    ----------
    adapter:
        A pre-configured V1Adapter, V2Adapter, or AutoAdapter.
    on_token_refresh:
        Optional async callback invoked after auto-refresh with the new Token.
    """

    def __init__(
        self,
        adapter: _AnyAdapter,
        *,
        on_token_refresh: Callable[[Token], Awaitable[None]] | None = None,
    ) -> None:
        self._adapter = adapter
        self._on_token_refresh = on_token_refresh

        # Lazily initialised resource instances
        self._auth: AuthResource | None = None
        self._account: AccountResource | None = None
        self._filesystem: FilesystemResource | None = None
        self._tasks: TasksResource | None = None
        self._downloads: DownloadsResource | None = None
        self._presentations: PresentationsResource | None = None
        self._subtitles: SubtitlesResource | None = None
        self._search: SearchResource | None = None

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_token(
        cls,
        access_token: str,
        *,
        refresh_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        on_token_refresh: Callable[[Token], Awaitable[None]] | None = None,
        timeout: float = 60.0,
    ) -> SeedrClient:
        """Create a client authenticated with a V2 OAuth access token.

        When ``refresh_token``, ``client_id``, and ``client_secret`` are
        supplied the client will automatically exchange the refresh token for a
        new access token on any 401/token-expired response and retry once.

        Parameters
        ----------
        access_token:
            A valid Seedr V2 OAuth access token.
        refresh_token:
            OAuth refresh token for automatic token refresh.
        client_id:
            OAuth client ID registered with Seedr.
        client_secret:
            OAuth client secret registered with Seedr.
        on_token_refresh:
            Async callback called after a successful refresh with the
            new :class:`~seedr_api.core.token.Token`.
        timeout:
            Total request timeout in seconds.

        Returns
        -------
        SeedrClient
        """
        adapter = _make_refreshing_v2_adapter(
            access_token,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            on_token_refresh=on_token_refresh,
            timeout=timeout,
        )
        return cls(adapter, on_token_refresh=on_token_refresh)

    @classmethod
    def from_v1_token(
        cls,
        access_token: str,
        *,
        refresh_token: str | None = None,
        client_id: str | None = None,
        on_token_refresh: Callable[[Token], Awaitable[None]] | None = None,
        timeout: float = 60.0,
    ) -> SeedrClient:
        """Create a client authenticated with a V1 access token.

        Parameters
        ----------
        access_token:
            A valid Seedr V1 OAuth access token.
        refresh_token:
            V1 refresh token for automatic token refresh.
        client_id:
            OAuth client ID (defaults to ``seedr_chrome``).
        on_token_refresh:
            Async callback called after a successful refresh.
        timeout:
            Total request timeout in seconds.

        Returns
        -------
        SeedrClient
        """
        adapter = _make_refreshing_v1_adapter(
            access_token,
            refresh_token=refresh_token,
            client_id=client_id or "seedr_chrome",
            on_token_refresh=on_token_refresh,
            timeout=timeout,
        )
        return cls(adapter, on_token_refresh=on_token_refresh)

    @classmethod
    def from_tokens(
        cls,
        *,
        v1_token: str | None = None,
        v2_token: str | None = None,
        v1_refresh_token: str | None = None,
        v2_refresh_token: str | None = None,
        client_id: str | None = None,
        on_token_refresh: Callable[[Token], Awaitable[None]] | None = None,
        timeout: float = 60.0,
    ) -> SeedrClient:
        """Create an AutoAdapter client using both V1 and V2 tokens.

        Parameters
        ----------
        v1_token:
            V1 access token.
        v2_token:
            V2 OAuth access token.
        v1_refresh_token:
            V1 refresh token.
        v2_refresh_token:
            V2 refresh token.
        client_id:
            OAuth client ID used for refresh.
        on_token_refresh:
            Async callback called after refresh.
        timeout:
            Total request timeout in seconds.

        Returns
        -------
        SeedrClient
        """
        from seedr_api.adapters.auto import AutoAdapter

        v1: V1Adapter | None = None
        v2: V2Adapter | None = None

        if v1_token is not None:
            v1 = _make_refreshing_v1_adapter(
                v1_token,
                refresh_token=v1_refresh_token,
                client_id=client_id or "seedr_chrome",
                on_token_refresh=on_token_refresh,
                timeout=timeout,
            )

        if v2_token is not None:
            v2 = _make_refreshing_v2_adapter(
                v2_token,
                refresh_token=v2_refresh_token,
                client_id=client_id,
                on_token_refresh=on_token_refresh,
                timeout=timeout,
            )

        adapter = AutoAdapter(v1=v1, v2=v2)
        return cls(adapter, on_token_refresh=on_token_refresh)

    @classmethod
    async def from_credentials(
        cls,
        username: str,
        password: str,
        *,
        client_id: str = "seedr_chrome",
        on_token_refresh: Callable[[Token], Awaitable[None]] | None = None,
        timeout: float = 60.0,
    ) -> SeedrClient:
        """Log in with username and password (V1 API) and return an authenticated client.

        This method performs the initial login automatically and sets up
        auto-refresh using the returned refresh token.

        Parameters
        ----------
        username:
            Seedr account username or email.
        password:
            Seedr account password.
        client_id:
            OAuth client ID. Defaults to ``seedr_chrome``.
        on_token_refresh:
            Async callback called after each token refresh.
        timeout:
            Total request timeout in seconds.

        Returns
        -------
        SeedrClient
            Authenticated client instance.
        """
        # Use a temporary V1 adapter to perform the login
        temp_v1 = V1Adapter("", timeout=timeout)
        try:
            token_resp = await temp_v1.login(username, password, client_id=client_id)
        finally:
            await temp_v1.close()

        return cls.from_v1_token(
            token_resp.access_token,
            refresh_token=token_resp.refresh_token,
            client_id=client_id,
            on_token_refresh=on_token_refresh,
            timeout=timeout,
        )

    @classmethod
    def anonymous(cls, *, timeout: float = 60.0) -> SeedrClient:
        """Create an unauthenticated client for auth-only operations.

        Useful for:
        - Starting the device code flow
        - Obtaining tokens before you have any

        Note: Most API calls will fail without authentication.

        Parameters
        ----------
        timeout:
            Total request timeout in seconds.

        Returns
        -------
        SeedrClient
            Unauthenticated client instance.
        """
        adapter = V1Adapter("", timeout=timeout)
        return cls(adapter)

    # ------------------------------------------------------------------
    # Async context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> SeedrClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying adapter and release connections."""
        await self._adapter.close()

    def __repr__(self) -> str:
        return f"SeedrClient(adapter={type(self._adapter).__name__!r})"

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    @property
    def access_token(self) -> str:
        """The current bearer token."""
        adapter = self._adapter
        if hasattr(adapter, "_access_token"):
            return adapter._access_token or ""
        return ""

    def update_token(self, access_token: str) -> None:
        """Replace the bearer token (e.g. after a manual token refresh)."""
        if hasattr(self._adapter, "update_token"):
            self._adapter.update_token(access_token)

    # ------------------------------------------------------------------
    # Resource accessors (lazy, cached)
    # ------------------------------------------------------------------

    @property
    def auth(self) -> AuthResource:
        """OAuth 2.0 token management and device code flow."""
        if self._auth is None:
            self._auth = AuthResource(self._adapter)
        return self._auth

    @property
    def account(self) -> AccountResource:
        """Account settings, devices, and wishlist."""
        if self._account is None:
            self._account = AccountResource(self._adapter)
        return self._account

    @property
    def filesystem(self) -> FilesystemResource:
        """Browse and manage files and folders."""
        if self._filesystem is None:
            self._filesystem = FilesystemResource(self._adapter)
        return self._filesystem

    @property
    def tasks(self) -> TasksResource:
        """Manage torrent download tasks."""
        if self._tasks is None:
            self._tasks = TasksResource(self._adapter)
        return self._tasks

    @property
    def downloads(self) -> DownloadsResource:
        """Stream files and retrieve download URLs."""
        if self._downloads is None:
            self._downloads = DownloadsResource(self._adapter)
        return self._downloads

    @property
    def presentations(self) -> PresentationsResource:
        """Media streaming URLs and playlists."""
        if self._presentations is None:
            self._presentations = PresentationsResource(self._adapter)
        return self._presentations

    @property
    def subtitles(self) -> SubtitlesResource:
        """List subtitles for files."""
        if self._subtitles is None:
            self._subtitles = SubtitlesResource(self._adapter)
        return self._subtitles

    @property
    def search(self) -> SearchResource:
        """Search your Seedr library."""
        if self._search is None:
            self._search = SearchResource(self._adapter)
        return self._search


# ------------------------------------------------------------------
# Internal helpers for building refreshing adapters
# ------------------------------------------------------------------

def _make_refreshing_v2_adapter(
    access_token: str,
    *,
    refresh_token: str | None,
    client_id: str | None,
    client_secret: str | None = None,
    on_token_refresh: Callable[[Token], Awaitable[None]] | None,
    timeout: float,
) -> V2Adapter:
    """Create a V2Adapter wrapped with auto-refresh logic."""

    class _RefreshingV2Adapter(V2Adapter):
        """V2Adapter that retries once after a token refresh on 401."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self._refresh_token_val: list[str | None] = [refresh_token]

        async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
            for attempt in range(2):
                try:
                    return await super()._request(method, path, **kwargs)
                except (TokenExpiredError, AuthenticationError):
                    if attempt == 0 and self._refresh_token_val[0] and client_id:
                        new_token = await self._do_refresh()
                        self.update_token(new_token)
                        continue
                    raise

        async def _do_refresh(self) -> str:
            if not self._refresh_token_val[0] or not client_id:
                raise AuthenticationError("No refresh token or client_id available")

            resp = await super().refresh_token(
                self._refresh_token_val[0],
                client_id,
                client_secret,
            )
            new_access = resp.access_token or ""
            new_refresh = resp.refresh_token
            if new_refresh:
                self._refresh_token_val[0] = new_refresh

            if on_token_refresh is not None:
                tok = Token.from_response(
                    new_access,
                    refresh_token=new_refresh or self._refresh_token_val[0],
                    expires_in=resp.expires_in,
                    client_id=client_id,
                )
                await on_token_refresh(tok)

            return new_access

    adapter = _RefreshingV2Adapter(access_token, timeout=timeout)
    return adapter


def _make_refreshing_v1_adapter(
    access_token: str,
    *,
    refresh_token: str | None,
    client_id: str,
    on_token_refresh: Callable[[Token], Awaitable[None]] | None,
    timeout: float,
) -> V1Adapter:
    """Create a V1Adapter wrapped with auto-refresh logic."""

    class _RefreshingV1Adapter(V1Adapter):
        """V1Adapter that retries once after a token refresh on auth errors."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self._refresh_token_val: list[str | None] = [refresh_token]

        async def _post_resource(self, func: str, **kwargs: Any) -> Any:
            for attempt in range(2):
                try:
                    return await super()._post_resource(func, **kwargs)
                except (TokenExpiredError, AuthenticationError):
                    # Catches both expired_token and invalid_token errors
                    if attempt == 0 and self._refresh_token_val[0]:
                        new_access = await self._do_refresh()
                        self.update_token(new_access)
                        continue
                    raise

        async def _do_refresh(self) -> str:
            if not self._refresh_token_val[0]:
                raise AuthenticationError("No refresh token available")

            resp = await super().refresh_token(
                self._refresh_token_val[0],
                client_id,
            )
            new_access = resp.access_token
            # V1 refresh does NOT return a new refresh_token — keep the old one

            if on_token_refresh is not None:
                tok = Token.from_response(
                    new_access,
                    refresh_token=self._refresh_token_val[0],
                    expires_in=resp.expires_in,
                    client_id=client_id,
                )
                await on_token_refresh(tok)

            return new_access

    adapter = _RefreshingV1Adapter(access_token, timeout=timeout)
    return adapter
