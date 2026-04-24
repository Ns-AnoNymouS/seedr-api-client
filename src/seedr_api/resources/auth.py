"""OAuth 2.0 resource — token management and device code flow."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import secrets
from typing import Any
from urllib.parse import urlencode

from seedr_api.exceptions import APIError, RateLimitError
from seedr_api.models.auth import (
    AuthorizationURL,
    DeviceCode,
    OAuthApp,
    PKCEChallenge,
    TokenResponse,
)
from seedr_api.resources._base import BaseResource

_SEEDR_HOST = "https://v2.seedr.cc"
_DEVICE_CODE_URL = f"{_SEEDR_HOST}/api/v0.1/p/oauth/device/code"
_DEVICE_TOKEN_URL = f"{_SEEDR_HOST}/api/v0.1/p/oauth/device/token"


class AuthResource(BaseResource):
    """Provides OAuth 2.0 authorization methods.

    Covers authorization code exchange (with PKCE), device code flow,
    client credentials flow, token revocation, and listing public OAuth apps.
    """

    async def get_apps(self) -> list[OAuthApp]:
        """Return a list of public OAuth applications registered with Seedr.

        Required scope: none (public endpoint)

        Returns
        -------
        list[OAuthApp]
            Public OAuth app metadata.
        """
        data: Any = await self._http.get("/oauth/apps")
        apps: list[Any] = data if isinstance(data, list) else data.get("apps", [])
        return [OAuthApp.model_validate(a) for a in apps]

    @staticmethod
    def generate_pkce_challenge(length: int = 64) -> PKCEChallenge:
        """Generate a random PKCE challenge for public clients.

        Parameters
        ----------
        length:
            Length of the code verifier (must be between 43 and 128).

        Returns
        -------
        PKCEChallenge
            The code verifier and its S256 challenge.
        """
        if not (43 <= length <= 128):
            raise ValueError("PKCE code verifier length must be between 43 and 128.")

        # urlsafe characters are A-Z, a-z, 0-9, -, _
        verifier = secrets.token_urlsafe(length)[:length]
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

        return PKCEChallenge(
            code_verifier=verifier,
            code_challenge=challenge,
            code_challenge_method="S256",
        )

    def generate_authorize_url(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        scope: str = "files.read profile",
        state: str | None = None,
        base_authorize_url: str = "https://v2.seedr.cc/api/v0.1/p/oauth/authorize",
    ) -> AuthorizationURL:
        """Generate an OAuth 2.0 authorization code URL for confidential clients.

        Parameters
        ----------
        client_id:
            OAuth client ID.
        redirect_uri:
            Callback URI to redirect the user back to.
        scope:
            Requested permissions, space-separated.
        state:
            Optional CSRF state token.
        base_authorize_url:
            Base authorize URL for Seedr API.

        Returns
        -------
        AuthorizationURL
            The constructed URL.
        """
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scope,
        }
        if state:
            params["state"] = state

        url = f"{base_authorize_url}?{urlencode(params)}"
        return AuthorizationURL(url=url)

    def generate_pkce_authorize_url(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        scope: str = "files.read profile",
        state: str | None = None,
        base_authorize_url: str = "https://v2.seedr.cc/api/v0.1/p/oauth/authorize",
    ) -> AuthorizationURL:
        """Generate a PKCE-secured authorization URL for public clients.

        Parameters
        ----------
        client_id:
            OAuth client ID.
        redirect_uri:
            Callback URI to redirect the user back to.
        scope:
            Requested permissions, space-separated.
        state:
            Optional CSRF state token.
        base_authorize_url:
            Base authorize URL for Seedr API.

        Returns
        -------
        AuthorizationURL
            The URL and the generated PKCE verifier needed for token exchange.
        """
        pkce = self.generate_pkce_challenge()
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scope,
            "code_challenge": pkce.code_challenge,
            "code_challenge_method": pkce.code_challenge_method,
        }
        if state:
            params["state"] = state

        url = f"{base_authorize_url}?{urlencode(params)}"
        return AuthorizationURL(url=url, pkce=pkce)

    async def revoke_token(self, *, token: str, client_id: str | None = None) -> None:
        """Revoke an access or refresh token.

        Required scope: none (uses the token being revoked)

        Parameters
        ----------
        token:
            The token to revoke.
        client_id:
            OAuth client ID. Required by the Seedr revocation endpoint.
        """
        data: dict[str, str] = {"token": token}
        if client_id is not None:
            data["client_id"] = client_id
        await self._http.post("/oauth/token/revoke_rfc7009", data=data)

    async def exchange_code(
        self,
        *,
        client_id: str,
        client_secret: str | None = None,
        code: str,
        redirect_uri: str,
        code_verifier: str | None = None,
    ) -> TokenResponse:
        """Exchange an authorization code (and optional PKCE verifier) for tokens.

        Parameters
        ----------
        client_id:
            OAuth client ID.
        client_secret:
            OAuth client secret (required for confidential clients).
        code:
            Authorization code received from the callback.
        redirect_uri:
            The redirect URI used in the authorization request.
        code_verifier:
            The PKCE verifier matching the challenge sent during authorization
            (required for public clients).

        Returns
        -------
        TokenResponse
            Access token (and optional refresh token).
        """
        data = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": code,
            "redirect_uri": redirect_uri,
        }
        if client_secret:
            data["client_secret"] = client_secret
        if code_verifier:
            data["code_verifier"] = code_verifier

        resp_data: Any = await self._http.post("/oauth/token", data=data)
        return TokenResponse.model_validate(resp_data)

    async def exchange_client_credentials(
        self,
        *,
        client_id: str,
        client_secret: str,
        scope: str = "files.read profile",
    ) -> TokenResponse:
        """Exchange client credentials directly for an access token.

        Best for server-to-server authentication. Returns an access token
        without a user context.

        Parameters
        ----------
        client_id:
            OAuth client ID.
        client_secret:
            OAuth client secret.
        scope:
            Requested permissions, space-separated.

        Returns
        -------
        TokenResponse
            Access token (without refresh token).
        """
        data: Any = await self._http.post(
            "/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": scope,
            },
        )
        return TokenResponse.model_validate(data)

    async def refresh_token(
        self,
        *,
        client_id: str,
        refresh_token: str,
        client_secret: str | None = None,
    ) -> TokenResponse:
        """Use a refresh token to obtain a new access token.

        Parameters
        ----------
        client_id:
            OAuth client ID.
        refresh_token:
            The refresh token to redeem.
        client_secret:
            OAuth client secret (required for confidential clients; omit for public clients).

        Returns
        -------
        TokenResponse
            New access and refresh tokens.
        """
        payload: dict[str, str] = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh_token,
        }
        if client_secret is not None:
            payload["client_secret"] = client_secret
        data: Any = await self._http.post("/oauth/token", data=payload)
        return TokenResponse.model_validate(data)

    async def request_device_code(
        self,
        *,
        client_id: str,
        scope: str = "profile account.read account.write settings.read settings.write files.read files.write tasks.read tasks.write archives.manage media.read subtitles.read subtitles.write",
    ) -> DeviceCode:
        """Initiate the device authorization flow.

        Display ``device_code.verification_uri`` and ``device_code.user_code``
        to the user, then call :meth:`poll_device_token` to obtain tokens.

        Parameters
        ----------
        client_id:
            OAuth client ID.

        Returns
        -------
        DeviceCode
            Verification URI, user code, and polling details.
        """
        data: Any = await self._http.post(
            _DEVICE_CODE_URL,
            data={"client_id": client_id, "scope": scope},
        )
        device = DeviceCode.model_validate(data)
        if device.verification_uri.startswith("/"):
            device = device.model_copy(
                update={"verification_uri": f"{_SEEDR_HOST}{device.verification_uri}"}
            )
        return device

    async def poll_device_token(
        self,
        *,
        client_id: str,
        device_code: str,
        interval: int = 5,
        max_wait: int = 300,
    ) -> TokenResponse:
        """Poll until the device is authorized and return the access token.

        Parameters
        ----------
        client_id:
            OAuth client ID.
        device_code:
            The device code from :meth:`request_device_code`.
        interval:
            Polling interval in seconds (defaults to the value from the
            device code response).
        max_wait:
            Maximum seconds to wait before raising :class:`TimeoutError`.

        Returns
        -------
        TokenResponse
            Access and refresh tokens once the user authorizes.

        Raises
        ------
        TimeoutError
            If the user does not authorize within *max_wait* seconds.
        APIError
            If the device code is denied.
        """
        elapsed = 0
        while elapsed < max_wait:
            await asyncio.sleep(interval)
            elapsed += interval
            try:
                data: Any = await self._http.post(
                    _DEVICE_TOKEN_URL,
                    data={
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        "client_id": client_id,
                        "device_code": device_code,
                    },
                )
                return TokenResponse.model_validate(data)
            except RateLimitError:
                interval += 5
                continue
            except APIError as exc:
                err = exc.message.lower()
                if "authorization_pending" in err or "slow_down" in err:
                    if "slow_down" in err:
                        interval += 5
                    continue
                raise
        raise TimeoutError("Device authorization timed out.")

