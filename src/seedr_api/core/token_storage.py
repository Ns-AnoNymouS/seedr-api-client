"""Token storage backends: in-memory and file-based."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Protocol, runtime_checkable

from seedr_api.core.token import Token


@runtime_checkable
class TokenStorageProtocol(Protocol):
    """Protocol for token storage backends."""

    async def load(self) -> Token | None:
        """Load and return the stored token, or None if not found."""
        ...

    async def save(self, token: Token) -> None:
        """Persist the token."""
        ...

    async def delete(self) -> None:
        """Delete the stored token."""
        ...


class MemoryTokenStorage:
    """In-memory token storage (non-persistent, useful for testing)."""

    def __init__(self) -> None:
        self._token: Token | None = None

    async def load(self) -> Token | None:
        """Return the in-memory token, or None."""
        return self._token

    async def save(self, token: Token) -> None:
        """Store the token in memory."""
        self._token = token

    async def delete(self) -> None:
        """Clear the stored token."""
        self._token = None


class FileTokenStorage:
    """File-based token storage using JSON.

    Parameters
    ----------
    path:
        Path to the JSON file where the token will be stored.
        The file and parent directories are created automatically on first save.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    async def load(self) -> Token | None:
        """Load the token from disk, returning None if the file does not exist."""
        try:
            data_str = await asyncio.to_thread(self._path.read_text, encoding="utf-8")
            data = json.loads(data_str)
            return Token.from_dict(data)
        except FileNotFoundError:
            return None
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    async def save(self, token: Token) -> None:
        """Write the token to disk as JSON, creating parent dirs if needed."""
        def _write() -> None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(token.to_dict(), indent=2),
                encoding="utf-8",
            )

        await asyncio.to_thread(_write)

    async def delete(self) -> None:
        """Remove the token file from disk."""
        def _remove() -> None:
            try:
                self._path.unlink()
            except FileNotFoundError:
                pass

        await asyncio.to_thread(_remove)
