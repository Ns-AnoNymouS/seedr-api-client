"""V1 auth models — strict Pydantic v2 models matching real API responses."""

from __future__ import annotations

from pydantic import BaseModel


class V1TokenResponse(BaseModel):
    """Token response from POST /oauth_test/token.php with grant_type=password.

    Real API shape:
    {access_token, expires_in, token_type, scope:null, refresh_token}
    """

    access_token: str
    expires_in: int
    token_type: str
    scope: str | None = None
    refresh_token: str


class V1RefreshToken(BaseModel):
    """Token response from POST /oauth_test/token.php with grant_type=refresh_token.

    Note: the API does NOT return a refresh_token in the response.
    Real API shape:
    {access_token, expires_in, token_type, scope:null}
    """

    access_token: str
    expires_in: int
    token_type: str
    scope: str | None = None


class V1DeviceCode(BaseModel):
    """Response from GET /api/device/code.

    Real API shape:
    {expires_in:1800, interval:5, device_code, user_code, verification_url}
    """

    expires_in: int
    interval: int
    device_code: str
    user_code: str
    verification_url: str
