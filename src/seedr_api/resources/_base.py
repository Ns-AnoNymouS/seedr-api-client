"""Base resource class shared by all API resource objects."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

# Union type alias for all adapter types
AnyAdapter = Any  # V1Adapter | V2Adapter | AutoAdapter


class BaseResource:
    """Base class for all API resource objects.

    Subclasses receive a reference to an adapter (V1, V2, or Auto) and
    use it to make authenticated requests.
    """

    def __init__(self, adapter: AnyAdapter) -> None:
        self._adapter = adapter
