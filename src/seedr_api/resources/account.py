"""Account resource — settings, devices, and wishlist."""

from __future__ import annotations

from typing import Any

from seedr_api.resources._base import BaseResource


class AccountResource(BaseResource):
    """Provides methods for account settings, devices, and wishlist management."""

    async def get_settings(self) -> Any:
        """Return account settings and profile information.

        Returns
        -------
        V1AccountSettings or V2AccountSettings
            Account settings including storage, bandwidth, and preferences.
        """
        return await self._adapter.get_settings()

    async def get_quota(self) -> Any:
        """Return storage and bandwidth quota.

        Returns
        -------
        V1MemoryBandwidth or V2Quota
            Space and bandwidth usage.
        """
        return await self._adapter.get_memory_bandwidth()

    async def get_devices(self) -> Any:
        """Return a list of registered devices.

        Returns
        -------
        list[V1Device]
            Registered device entries (V1 only; V2 returns empty list).
        """
        return await self._adapter.get_devices()

    async def get_wishlist(self) -> Any:
        """Return the wishlist.

        Returns
        -------
        list[V1WishlistItem] or list[V2WishlistItem]
            Wishlist entries.
        """
        return await self._adapter.get_wishlist()

    async def delete_wishlist_item(self, wishlist_id: int) -> Any:
        """Delete a wishlist entry.

        Parameters
        ----------
        wishlist_id:
            The numeric wishlist item ID.

        Returns
        -------
        dict
            Deletion result.
        """
        return await self._adapter.delete_wishlist_item(wishlist_id)

