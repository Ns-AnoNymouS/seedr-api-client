"""Pydantic v2 models for Seedr API responses — user/account domain."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    """Seedr user profile information."""

    id: int | None = None
    username: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    package_name: str | None = None


class Quota(BaseModel):
    """Storage and bandwidth quota for the authenticated user."""

    space_max: int | None = None
    space_used: int | None = None
    bandwidth_max: int | None = None
    bandwidth_used: int | None = None


class UserSettings(BaseModel):
    """Application-specific settings for the authenticated user."""

    settings: dict[str, Any] = Field(default_factory=dict)
