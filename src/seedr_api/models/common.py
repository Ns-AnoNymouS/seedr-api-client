"""Common utilities shared across V1 and V2 models."""

from __future__ import annotations

from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class APIVersion(str, Enum):
    """Which API version to use."""

    V1 = "v1"
    V2 = "v2"
    AUTO = "auto"


def _safe_parse(model_cls: type[T], data: Any) -> T | None:
    """Lenient model parse — returns None on any validation error.

    Intended for V2 models only, where missing/unknown fields are normal.
    """
    try:
        return model_cls.model_validate(data)
    except Exception:
        return None


def _safe_parse_list(model_cls: type[T], items: list[Any]) -> list[T]:
    """Parse a list of dicts into model instances, silently dropping failures."""
    result: list[T] = []
    for item in items:
        parsed = _safe_parse(model_cls, item)
        if parsed is not None:
            result.append(parsed)
    return result
