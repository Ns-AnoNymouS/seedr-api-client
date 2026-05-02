"""Auth resource — token management, device code flow, and OAuth operations."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import secrets
from typing import Any
from urllib.parse import urlencode

from seedr_api.exceptions import APIError, RateLimitError
from seedr_api.resources._base import BaseResource

_SEEDR_HOST = "https://v2.seedr.cc"


class AuthResource(BaseResource):
    """Provides OAuth 2.0 authorization methods.

    Works with both V1 and V2 adapters.
    Covers device code flow, PKCE helpers, token operations.
    """

    @staticmethod
    def generate_pkce_challenge(length: int = 64) -> dict[str, str]:
        """Generate a random PKCE challenge for public clients.

        Parameters
        ----------
        length:
            Length of the code verifier (must be between 43 and 128).

        Returns
        -------
        dict
            Contains ``code_verifier``, ``code_challenge``, and
            ``code_challenge_method``.
        """
        if not (43 <= length <= 128):
            raise ValueError("PKCE code verifier length must be between 43 and 128.")
        verifier = secrets.token_urlsafe(length)[:length]
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return {
            "code_verifier": verifier,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }

    def generate_authorize_url(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        scope: str = "files.read profile",
        state: str | None = None,
        base_authorize_url: str = f"{_SEEDR_HOST}/api/v0.1/p/oauth/authorize",
    ) -> str:
        """Generate an OAuth 2.0 authorization code URL.

        Parameters
        ----------
        client_id:
            OAuth client ID.
        redirect_uri:
            Callback URI.
        scope:
            Requested permissions.
        state:
            Optional CSRF state token.
        base_authorize_url:
            Base authorize URL.

        Returns
        -------
        str
            The constructed authorization URL.
        """
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scope,
        }
        if state:
            params["state"] = state
        return f"{base_authorize_url}?{urlencode(params)}"

    def generate_pkce_authorize_url(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        scope: str = "files.read profile",
        state: str | None = None,
        base_authorize_url: str = f"{_SEEDR_HOST}/api/v0.1/p/oauth/authorize",
    ) -> dict[str, str]:
        """Generate a PKCE-secured authorization URL.

        Returns
        -------
        dict
            Contains ``url`` and PKCE challenge fields.
        """
        pkce = self.generate_pkce_challenge()
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scope,
            "code_challenge": pkce["code_challenge"],
            "code_challenge_method": pkce["code_challenge_method"],
        }
        if state:
            params["state"] = state
        url = f"{base_authorize_url}?{urlencode(params)}"
        return {"url": url, **pkce}

    async def login(self, username: str, password: str) -> Any:
        """Authenticate with username and password (V1 only).

        Parameters
        ----------
        username:
            Seedr account username or email.
        password:
            Seedr account password.

        Returns
        -------
        V1TokenResponse
            Access token and refresh token.
        """
        return await self._adapter.login(username, password)

    async def refresh_token(
        self,
        refresh_token: str,
        client_id: str,
    ) -> Any:
        """Use a refresh token to get a new access token.

        Parameters
        ----------
        refresh_token:
            The refresh token to redeem.
        client_id:
            OAuth client ID.

        Returns
        -------
        Token response with new access token.
        """
        return await self._adapter.refresh_token(refresh_token, client_id)

    async def request_device_code(self, client_id: str) -> Any:
        """Initiate the device authorization flow.

        Display the verification URL and user code to the user, then
        poll with :meth:`poll_device_token`.

        Parameters
        ----------
        client_id:
            OAuth client ID.

        Returns
        -------
        Device code response.
        """
        return await self._adapter.get_device_code(client_id)

    async def poll_device_token(
        self,
        *,
        client_id: str,
        device_code: str,
        interval: int = 5,
        max_wait: int = 300,
    ) -> Any:
        """Poll until the device is authorized and return the access token.

        Parameters
        ----------
        client_id:
            OAuth client ID.
        device_code:
            The device code from :meth:`request_device_code`.
        interval:
            Polling interval in seconds.
        max_wait:
            Maximum seconds to wait before raising :class:`TimeoutError`.

        Returns
        -------
        Token response once the user authorizes.

        Raises
        ------
        TimeoutError
            If the user does not authorize within *max_wait* seconds.
        """
        elapsed = 0
        while elapsed < max_wait:
            await asyncio.sleep(interval)
            elapsed += interval
            try:
                return await self._adapter.authorize_device(device_code, client_id)
            except RateLimitError:
                interval += 5
                continue
            except APIError as exc:
                if exc.status_code == 202:  # authorization_pending
                    continue
                if exc.status_code == 429:  # slow_down
                    interval += 5
                    continue
                raise
        raise TimeoutError("Device authorization timed out.")
