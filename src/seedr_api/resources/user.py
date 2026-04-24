"""User resource — profile, quota, and settings."""

from __future__ import annotations

from typing import Any

from seedr_api.models.user import Quota, UserInfo, UserSettings
from seedr_api.resources._base import BaseResource


class UserResource(BaseResource):
    """Provides methods to retrieve user account information."""

    async def get(self) -> UserInfo:
        """Return the authenticated user's profile.

        Required scope: ``profile``

        Returns
        -------
        UserInfo
            User profile data (id, email, username, etc.).
        """
        data: Any = await self._http.get("/user")
        profile = data.get("profile", data) if isinstance(data, dict) else data
        return UserInfo.model_validate(profile)

    async def get_quota(self) -> Quota:
        """Return storage and bandwidth quota information.

        Required scope: ``account.read``

        Returns
        -------
        Quota
            Space and bandwidth limits and current usage.
        """
        data: Any = await self._http.get("/me/quota")
        return Quota.model_validate(data)

    async def get_settings(self) -> UserSettings:
        """Return application-specific user settings.

        Required scope: ``settings.read``

        Returns
        -------
        UserSettings
            All persisted user settings as a dictionary.
        """
        data: Any = await self._http.get("/me/settings")
        if isinstance(data, dict) and "settings" not in data:
            return UserSettings(settings=data)
        return UserSettings.model_validate(data)
