"""SeedrClient — main entry point for the seedr-api library.

Usage::

    # OAuth token
    async with SeedrClient.from_token("access_token") as client:
        root = await client.filesystem.list_root_contents()

    # Email / password
    async with SeedrClient.from_credentials("you@example.com", "secret") as client:
        user = await client.user.get()
"""

from __future__ import annotations

import aiohttp

from seedr_api._http import AsyncHTTPClient
from seedr_api.exceptions import SeedrError
from seedr_api.resources.auth import AuthResource
from seedr_api.resources.downloads import DownloadsResource
from seedr_api.resources.filesystem import FilesystemResource
from seedr_api.resources.presentations import PresentationsResource
from seedr_api.resources.search import SearchResource
from seedr_api.resources.subtitles import SubtitlesResource
from seedr_api.resources.tasks import TasksResource
from seedr_api.resources.user import UserResource

#: OAuth base URL (used with bearer tokens)
_OAUTH_BASE = "https://www.seedr.cc/api/v0.1"

#: Password-auth base URL (used with HTTP Basic Auth)
_PASSWORD_BASE = "https://www.seedr.cc/api/v0.1/p"


class SeedrClient:
    """Async client for the Seedr API.

    Do **not** instantiate this class directly. Use the class-method
    constructors :meth:`from_token` or :meth:`from_credentials`.

    Parameters
    ----------
    http:
        Pre-configured :class:`~seedr._http.AsyncHTTPClient` instance.
    """

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

        # Lazily initialised resource instances
        self._auth: AuthResource | None = None
        self._filesystem: FilesystemResource | None = None
        self._tasks: TasksResource | None = None
        self._downloads: DownloadsResource | None = None
        self._presentations: PresentationsResource | None = None
        self._subtitles: SubtitlesResource | None = None
        self._search: SearchResource | None = None
        self._user: UserResource | None = None

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_token(
        cls,
        access_token: str,
        *,
        timeout: float = 60.0,
    ) -> SeedrClient:
        """Create a client authenticated with an OAuth 2.0 access token.

        Parameters
        ----------
        access_token:
            A valid Seedr OAuth access token.
        timeout:
            Total request timeout in seconds. Defaults to 60.

        Returns
        -------
        SeedrClient
            Configured client instance.
        """
        http = AsyncHTTPClient(
            _OAUTH_BASE,
            access_token=access_token,
            timeout=aiohttp.ClientTimeout(total=timeout),
        )
        return cls(http)

    @classmethod
    def from_credentials(
        cls,
        email: str,
        password: str,
        *,
        timeout: float = 60.0,
    ) -> SeedrClient:
        """Create a client authenticated with an email and password.

        Parameters
        ----------
        email:
            Seedr account email address.
        password:
            Seedr account password.
        timeout:
            Total request timeout in seconds. Defaults to 60.

        Returns
        -------
        SeedrClient
            Configured client instance.
        """
        http = AsyncHTTPClient(
            _PASSWORD_BASE,
            basic_auth=(email, password),
            timeout=aiohttp.ClientTimeout(total=timeout),
        )
        return cls(http)

    @classmethod
    async def login_with_client_credentials(
        cls,
        client_id: str,
        client_secret: str,
        scope: str = "files.read profile",
        *,
        timeout: float = 60.0,
    ) -> SeedrClient:
        """Log in directly using OAuth 2.0 client credentials.

        Best for server-to-server APIs. Fetches a new access token
        under the hood and returns an authenticated client instance.

        Parameters
        ----------
        client_id:
            OAuth client ID.
        client_secret:
            OAuth client secret.
        scope:
            Requested permissions, space-separated.
        timeout:
            Total request timeout in seconds. Defaults to 60.

        Returns
        -------
        SeedrClient
            Configured client instance authenticated with the generated token.
        """
        # Create a temporary unauthenticated client to fetch the token
        http = AsyncHTTPClient(
            _OAUTH_BASE,
            timeout=aiohttp.ClientTimeout(total=timeout),
        )
        temp_client = cls(http)

        # Exchange credentials for an access token
        try:
            token = await temp_client.auth.exchange_client_credentials(
                client_id=client_id,
                client_secret=client_secret,
                scope=scope,
            )
            # Update the token on the HTTP client so the user gets a working instance
            temp_client.update_token(token.access_token)
            return temp_client
        except (SeedrError, aiohttp.ClientError):
            await temp_client.close()
            raise

    # ------------------------------------------------------------------
    # Async context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> SeedrClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP session and release connections."""
        await self._http.close()

    def __repr__(self) -> str:
        auth_method = "token" if self._http._access_token else "basic_auth"
        return f"SeedrClient(base_url={self._http._base_url!r}, auth={auth_method!r})"

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def update_token(self, access_token: str) -> None:
        """Replace the bearer token (e.g. after a token refresh).

        Parameters
        ----------
        access_token:
            New access token.
        """
        self._http.update_token(access_token)

    # ------------------------------------------------------------------
    # Resource accessors (lazy, cached)
    # ------------------------------------------------------------------

    @property
    def auth(self) -> AuthResource:
        """OAuth 2.0 token management and device code flow."""
        if self._auth is None:
            self._auth = AuthResource(self._http)
        return self._auth

    @property
    def filesystem(self) -> FilesystemResource:
        """Browse and manage files and folders."""
        if self._filesystem is None:
            self._filesystem = FilesystemResource(self._http)
        return self._filesystem

    @property
    def tasks(self) -> TasksResource:
        """Manage torrent download tasks."""
        if self._tasks is None:
            self._tasks = TasksResource(self._http)
        return self._tasks

    @property
    def downloads(self) -> DownloadsResource:
        """Stream files and retrieve download URLs."""
        if self._downloads is None:
            self._downloads = DownloadsResource(self._http)
        return self._downloads

    @property
    def presentations(self) -> PresentationsResource:
        """Media streaming URLs and playlists."""
        if self._presentations is None:
            self._presentations = PresentationsResource(self._http)
        return self._presentations

    @property
    def subtitles(self) -> SubtitlesResource:
        """List, upload, and search subtitles."""
        if self._subtitles is None:
            self._subtitles = SubtitlesResource(self._http)
        return self._subtitles

    @property
    def search(self) -> SearchResource:
        """Search your Seedr library and scrape webpages for magnets."""
        if self._search is None:
            self._search = SearchResource(self._http)
        return self._search

    @property
    def user(self) -> UserResource:
        """User profile, quota, and settings."""
        if self._user is None:
            self._user = UserResource(self._http)
        return self._user
