"""Adapter layer: V1, V2, and Auto adapters."""

from __future__ import annotations

from seedr_api.adapters.auto import AutoAdapter
from seedr_api.adapters.base import SeedrAdapter
from seedr_api.adapters.v1 import V1Adapter
from seedr_api.adapters.v2 import V2Adapter

__all__ = [
    "AutoAdapter",
    "SeedrAdapter",
    "V1Adapter",
    "V2Adapter",
]
