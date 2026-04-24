"""Pydantic v2 models for Seedr API responses — auth/OAuth domain."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OAuthApp(BaseModel):
    """Represents a public OAuth application registered with Seedr."""

    client_id: str
    name: str
    description: str | None = None
    homepage_url: str | None = None
    logo_url: str | None = None
    category: str | None = None
    developer_name: str | None = None
    developer_email: str | None = None
    privacy_policy_url: str | None = None
    terms_url: str | None = None


class DeviceCode(BaseModel):
    """Response from the device code initiation endpoint."""

    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int = Field(default=5, description="Poll interval in seconds")


class TokenResponse(BaseModel):
    """OAuth token response (authorization code, device, and client-credentials flows)."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None
    user_id: str | None = None


class PKCEChallenge(BaseModel):
    """PKCE challenge data for public clients."""

    code_verifier: str
    code_challenge: str
    code_challenge_method: str = "S256"


class AuthorizationURL(BaseModel):
    """Authorization URL and optional generated PKCE data."""

    url: str
    pkce: PKCEChallenge | None = None
