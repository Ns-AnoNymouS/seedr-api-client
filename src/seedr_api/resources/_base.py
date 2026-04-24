"""Base resource class shared by all API resource objects."""

from __future__ import annotations

from seedr_api._http import AsyncHTTPClient


class BaseResource:
    """Base class for all API resource objects.

    Subclasses receive a reference to the shared :class:`AsyncHTTPClient`
    and use it to make authenticated requests.
    """

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http
