"""V1 account/settings models — strict Pydantic v2 models matching real API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class V1WishlistItem(BaseModel):
    """A wishlist entry returned inside get_settings.account.wishlist."""

    model_config = ConfigDict(extra="ignore")

    id: int
    user_id: int
    title: str
    size: int
    torrent_hash: str
    torrent_magnet: str
    created: str
    added: int
    is_private: int


class _V1Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    allow_remote_access: int | None = None
    site_language: str | None = None
    subtitles_language: str | None = None
    email_announcements: int | None = None
    email_newsletter: int | None = None


class _V1Account(BaseModel):
    model_config = ConfigDict(extra="ignore")

    username: str
    email: str
    user_id: int
    premium: bool
    space_used: int
    space_max: int
    space_scope: str
    bandwidth_used: int
    package_id: int
    package_name: str
    wishlist: list[V1WishlistItem]
    invites: int
    invites_accepted: int


class V1AccountSettings(BaseModel):
    """Full response from resource.php?func=get_settings.

    Real API shape:
    {settings:{...}, account:{...}, country:str, result:true}
    """

    model_config = ConfigDict(extra="ignore")

    settings: _V1Settings
    account: _V1Account
    country: str
    result: bool


class V1MemoryBandwidth(BaseModel):
    """Response from resource.php?func=get_memory_bandwidth.

    Real API shape:
    {bandwidth_used, bandwidth_max, space_used, space_max, space_scope, is_premium, result}
    """

    model_config = ConfigDict(extra="ignore")

    bandwidth_used: int
    bandwidth_max: int
    space_used: int
    space_max: int
    space_scope: str
    is_premium: bool
    result: bool


class V1Device(BaseModel):
    """A single device entry from get_devices response."""

    model_config = ConfigDict(extra="ignore")

    client_id: str
    client_name: str
    device_code: str
    tk: str | None = None
