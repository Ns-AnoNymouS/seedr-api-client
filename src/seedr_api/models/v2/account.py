"""V2 account models — lenient, all Optional."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class V2WishlistItem(BaseModel):
    """A wishlist entry returned in queue-full (413) responses."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    user_id: int | None = None
    title: str | None = None
    size: int | None = None
    torrent_hash: str | None = None
    torrent_magnet: str | None = None
    torrent_meta: str | None = None
    created: str | None = None
    added: int | None = None
    is_private: int | None = None


class V2AccountSettings(BaseModel):
    """Response from GET /me/settings (flat object)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    subtitles_language: str | None = None
    site_language: str | None = None
    email_newsletter: int | None = None
    email_announcements: int | None = None
    email_task_notifications_enabled: bool | None = None
    select_files_on_task_add: int | None = None
    user_id: int | None = Field(None, alias="userId")


class V2Quota(BaseModel):
    """Response from GET /me/quota."""

    model_config = ConfigDict(extra="ignore")

    bandwidth_used: int | None = None
    bandwidth_max: int | None = None
    space_used: int | None = None
    space_max: int | None = None
    space_scope: str | None = None
    is_premium: bool | None = None


class _V2UserStorageInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    limit: int | None = None
    used: int | None = None
    scope: str | None = None
    pool_name: str | None = None

    @property
    def max(self) -> int | None:
        return self.limit


class _V2UserFeatures(BaseModel):
    model_config = ConfigDict(extra="ignore")

    max_torrents: int | None = None
    active_torrents: int | None = None
    max_wishlist: int | None = None
    concurrent_downloads: int | None = None


class _V2UserAccount(BaseModel):
    model_config = ConfigDict(extra="ignore")

    is_premium: bool | None = None
    storage: _V2UserStorageInfo | None = None
    features: _V2UserFeatures | None = None


class _V2UserProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    email: str | None = None
    username: str | None = None
    created_at: int | None = None
    last_login: int | None = None


class V2AccountInfo(BaseModel):
    """Response from GET /user.

    Shape: {profile: {id, email, username, created_at, last_login},
            account: {is_premium, storage: {limit, used, scope, pool_name},
                      features: {max_torrents, active_torrents, max_wishlist,
                                 concurrent_downloads}}}
    """

    model_config = ConfigDict(extra="ignore")

    profile: _V2UserProfile | None = None
    account: _V2UserAccount | None = None

    @property
    def email(self) -> str | None:
        return self.profile.email if self.profile else None

    @property
    def id(self) -> int | None:
        return self.profile.id if self.profile else None

    @property
    def storage(self) -> _V2UserStorageInfo | None:
        return self.account.storage if self.account else None
