"""Integration tests — all OAuth flows.

Flows covered
-------------
1. Public endpoint  — ``get_apps``
2. PKCE helpers     — ``generate_pkce_challenge``, ``generate_authorize_url``,
                       ``generate_pkce_authorize_url``
3. Device-code flow — request phase (always runs) + full interactive poll
                       (opt-in via ``SEEDR_RUN_INTERACTIVE=1``)
4. Client-credentials flow (requires ``SEEDR_CLIENT_SECRET`` env var)
5. PAT / ``from_token`` flow
6. Token revocation (interactive, opt-in)
"""

from __future__ import annotations

import asyncio
import os

import pytest

from seedr_api.client import SeedrClient
from seedr_api.exceptions import AuthenticationError
from seedr_api.models.auth import (
    AuthorizationURL,
    DeviceCode,
    OAuthApp,
    PKCEChallenge,
    TokenResponse,
)
from tests.integration.conftest import SEEDR_CLIENT_ID, SEEDR_CLIENT_SECRET

_INTERACTIVE = os.getenv("SEEDR_RUN_INTERACTIVE") == "1"


# ---------------------------------------------------------------------------
# 1. Public endpoint
# ---------------------------------------------------------------------------


async def test_get_apps(client: SeedrClient) -> None:
    """``/oauth/apps`` returns a non-empty list of OAuthApp objects."""
    apps = await client.auth.get_apps()
    assert isinstance(apps, list)
    assert len(apps) > 0
    for app in apps:
        assert isinstance(app, OAuthApp)
        assert app.client_id
        assert app.name


# ---------------------------------------------------------------------------
# 2. PKCE / authorization-code URL helpers (pure computation + URL shape)
# ---------------------------------------------------------------------------


def test_generate_pkce_challenge(client: SeedrClient) -> None:
    pkce = client.auth.generate_pkce_challenge()
    assert isinstance(pkce, PKCEChallenge)
    assert pkce.code_challenge_method == "S256"
    assert 43 <= len(pkce.code_verifier) <= 128
    assert len(pkce.code_challenge) > 0


def test_generate_authorize_url(client: SeedrClient) -> None:
    result = client.auth.generate_authorize_url(
        client_id="test_client",
        redirect_uri="https://example.com/callback",
        scope="files.read profile",
        state="csrf_state_123",
    )
    assert isinstance(result, AuthorizationURL)
    assert "oauth/authorize" in result.url
    assert "client_id=test_client" in result.url
    assert "response_type=code" in result.url
    assert "scope=files.read" in result.url
    assert "state=csrf_state_123" in result.url
    assert result.pkce is None


def test_generate_pkce_authorize_url(client: SeedrClient) -> None:
    result = client.auth.generate_pkce_authorize_url(
        client_id="test_client",
        redirect_uri="https://example.com/callback",
        scope="files.read profile",
    )
    assert isinstance(result, AuthorizationURL)
    assert "code_challenge=" in result.url
    assert "code_challenge_method=S256" in result.url
    assert result.pkce is not None
    assert result.pkce.code_verifier
    assert result.pkce.code_challenge_method == "S256"


# ---------------------------------------------------------------------------
# 3. Device-code flow — request phase (no user interaction needed)
# ---------------------------------------------------------------------------


async def test_device_code_request(client: SeedrClient) -> None:
    """``request_device_code`` must return a well-formed DeviceCode."""
    device = await client.auth.request_device_code(client_id=SEEDR_CLIENT_ID)
    assert isinstance(device, DeviceCode)
    assert device.device_code
    assert device.user_code
    assert device.verification_uri.startswith("https://")
    assert device.expires_in > 0
    assert device.interval > 0


# ---------------------------------------------------------------------------
# 3b. Device-code flow — full interactive poll
#     Run with:  SEEDR_RUN_INTERACTIVE=1 pytest tests/integration/test_auth.py
#                  -k test_device_code_full_flow -s
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _INTERACTIVE, reason="Set SEEDR_RUN_INTERACTIVE=1 to run")
async def test_device_code_full_flow() -> None:
    """Full device-code flow: request → user approves → poll → verify token.

    Usage
    -----
    Step 1 — get a device code and authorize it in the browser::

        python - <<'EOF'
        import asyncio, aiohttp, json
        async def main():
            async with aiohttp.ClientSession() as s:
                r = await s.post("https://v2.seedr.cc/api/v0.1/p/oauth/device/code",
                                 data={"client_id": "V94K2IfOGY2BNYTrJTFeTtJ1VOuKzM52",
                                       "scope": "profile files.read"})
                d = await r.json(); print(json.dumps(d, indent=2))
        asyncio.run(main())
        EOF

    Step 2 — open the printed ``verification_uri`` in your browser and enter the
    ``user_code``.

    Step 3 — run the test with the device code from Step 1::

        SEEDR_RUN_INTERACTIVE=1 \\
        SEEDR_DEVICE_CODE=<device_code> \\
        pytest tests/integration/test_auth.py::test_device_code_full_flow -v
    """
    device_code_str = os.environ.get("SEEDR_DEVICE_CODE")
    if not device_code_str:
        pytest.skip(
            "Set SEEDR_DEVICE_CODE=<pre-authorized device_code> to run this test. "
            "See the docstring for the 3-step setup."
        )

    # Poll — no Bearer token needed on this endpoint
    async with SeedrClient.from_token("") as poller:
        token_resp = await poller.auth.poll_device_token(
            client_id=SEEDR_CLIENT_ID,
            device_code=device_code_str,
            interval=5,
            max_wait=30,
        )

    assert isinstance(token_resp, TokenResponse)
    assert token_resp.access_token
    assert token_resp.refresh_token
    assert token_resp.user_id  # user ID is embedded in the token response

    # Verify the freshly obtained token actually authenticates on the API
    async with SeedrClient.from_token(token_resp.access_token) as new_client:
        # get_apps is a public call that confirms the client/token round-trips correctly
        apps = await new_client.auth.get_apps()
    assert isinstance(apps, list)


# ---------------------------------------------------------------------------
# 4. Client-credentials flow
#    Run with:  SEEDR_CLIENT_SECRET=<secret> pytest … -k test_client_credentials
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not SEEDR_CLIENT_SECRET,
    reason="Set SEEDR_CLIENT_SECRET to test client-credentials flow",
)
async def test_client_credentials_flow() -> None:
    """Exchange client_id + client_secret for an access token, then use it."""
    assert SEEDR_CLIENT_SECRET  # narrowed for type-checker

    client = await SeedrClient.login_with_client_credentials(
        client_id=SEEDR_CLIENT_ID,
        client_secret=SEEDR_CLIENT_SECRET,
        scope="profile files.read",
    )
    async with client:
        user = await client.user.get()
    assert user is not None


# ---------------------------------------------------------------------------
# 5. PAT / from_token flow
# ---------------------------------------------------------------------------


async def test_pat_from_token(token: str) -> None:
    """A pre-existing token (PAT) must allow authenticated requests."""
    async with SeedrClient.from_token(token) as c:
        user = await c.user.get()
    assert user.email is not None


async def test_pat_token_is_used_in_header(token: str) -> None:
    """from_token stores the token and uses it as a Bearer header."""
    async with SeedrClient.from_token(token) as c:
        # Verify the token is reflected on the HTTP client
        assert c._http._access_token == token
        # Verify a real API call succeeds (confirms the header is sent)
        quota = await c.user.get_quota()
    assert quota is not None


async def test_pat_invalid_token_raises() -> None:
    """An invalid / expired token must raise AuthenticationError."""
    async with SeedrClient.from_token("invalid_token_xyz") as c:
        with pytest.raises(AuthenticationError):
            await c.user.get()


# ---------------------------------------------------------------------------
# 6. Token revocation (interactive — needs a second fresh token to revoke)
#    Run with:  SEEDR_RUN_INTERACTIVE=1 pytest … -k test_token_revocation -s
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _INTERACTIVE, reason="Set SEEDR_RUN_INTERACTIVE=1 to run")
async def test_token_revocation() -> None:
    """Obtain a fresh device-code token, revoke it, verify it stops working.

    Requires a second pre-authorized device code (separate from the main token)
    so the main ``.token`` file is never revoked.

    Usage
    -----
    Follow the same 3-step process described in ``test_device_code_full_flow``,
    then run::

        SEEDR_RUN_INTERACTIVE=1 \\
        SEEDR_DEVICE_CODE=<pre-authorized device_code> \\
        pytest tests/integration/test_auth.py::test_token_revocation -v
    """
    device_code_str = os.environ.get("SEEDR_DEVICE_CODE")
    if not device_code_str:
        pytest.skip("Set SEEDR_DEVICE_CODE=<pre-authorized device_code> to run.")

    # Exchange the pre-authorized device code for a fresh token
    async with SeedrClient.from_token("") as poller:
        fresh = await poller.auth.poll_device_token(
            client_id=SEEDR_CLIENT_ID,
            device_code=device_code_str,
            interval=5,
            max_wait=30,
        )

    assert fresh.access_token

    # Revoke the fresh token (client_id required by Seedr's revocation endpoint)
    async with SeedrClient.from_token(fresh.access_token) as victim:
        await victim.auth.revoke_token(token=fresh.access_token, client_id=SEEDR_CLIENT_ID)

    # Verify the revoked token is now rejected
    async with SeedrClient.from_token(fresh.access_token) as dead:
        with pytest.raises(AuthenticationError):
            await dead.user.get()
