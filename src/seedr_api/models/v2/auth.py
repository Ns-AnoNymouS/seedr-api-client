"""V2 auth models — lenient, all Optional."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class V2TokenResponse(BaseModel):
    """OAuth token response from V2 endpoints."""

    model_config = ConfigDict(extra="ignore")

    access_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None
    user_id: str | None = None


class V2DeviceCode(BaseModel):
    """Device code response from V2 OAuth device flow."""

    model_config = ConfigDict(extra="ignore")

    device_code: str | None = None
    user_code: str | None = None
    verification_uri: str | None = None
    verification_uri_complete: str | None = None
    expires_in: int | None = None
    interval: int | None = None
