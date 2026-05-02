# seedr-api-client

[![PyPI](https://img.shields.io/pypi/v/seedr-api-client)](https://pypi.org/project/seedr-api-client/)
[![Python](https://img.shields.io/pypi/pyversions/seedr-api-client)](https://pypi.org/project/seedr-api-client/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A fully async Python client for the [Seedr](https://www.seedr.cc) API — supports **both V1** (stable, `resource.php` + OAuth) **and V2** (alpha, REST) with strict/lenient models respectively, auto token refresh, multiple usage patterns, and complete type annotations.

---

## Installation

```bash
pip install seedr-api-client
```

**Requires:** Python 3.10+, `aiohttp>=3.9`, `pydantic>=2.0`

---

## Quick Start

```python
import asyncio
from seedr_api import SeedrClient

async def main():
    async with SeedrClient.from_token("your-access-token") as client:
        root = await client.filesystem.list_root_contents()
        for folder in root.folders or []:
            print(folder.path)

asyncio.run(main())
```

---

## Authentication

### Username + Password (V1)

```python
from seedr_api import SeedrClient

client = await SeedrClient.from_credentials("user@example.com", "password")
```

### Device Code Flow (CLI / TV apps)

```python
client = SeedrClient.anonymous()

code = await client.auth.request_device_code("seedr_xbmc")
print(f"Visit: {code.verification_url}")
print(f"Code:  {code.user_code}")

token = await client.auth.poll_device_token("seedr_xbmc", code.device_code)
print(f"Access token: {token.access_token}")
```

### Auto Token Refresh

```python
async def save_token(token):
    # persist token.access_token and token.refresh_token somewhere
    pass

client = SeedrClient.from_token(
    access_token="...",
    refresh_token="...",
    client_id="seedr_chrome",
    on_token_refresh=save_token,
)
```

---

## Usage Patterns

### 1. Async Context Manager (recommended)

```python
async with SeedrClient.from_token("access-token") as client:
    root = await client.filesystem.list_root_contents()
```

### 2. Persistent Object

```python
client = SeedrClient.from_token("access-token")
try:
    root = await client.filesystem.list_root_contents()
finally:
    await client.close()
```

### 3. With Auto Token Refresh

```python
async def on_refresh(token):
    save_to_disk(token.access_token, token.refresh_token)

async with SeedrClient.from_token(
    "access-token",
    refresh_token="refresh-token",
    client_id="seedr_chrome",
    on_token_refresh=on_refresh,
) as client:
    ...
```

### 4. Credentials Login (V1)

```python
client = await SeedrClient.from_credentials("user@example.com", "password")
async with client:
    quota = await client.account.get_quota()
    print(f"Used: {quota.space_used} / {quota.space_max}")
```

### 5. V1-Only Client

```python
client = SeedrClient.from_v1_token("v1-access-token")
devices = await client.account.get_devices()   # V1-exclusive
```

### 6. Both V1 + V2 (AutoAdapter)

```python
client = SeedrClient.from_tokens(
    v1_token="v1-token",
    v2_token="v2-token",
)
```

### 7. Fluent Builder

```python
from seedr_api import SeedrClientBuilder
from seedr_api.core.token_storage import FileTokenStorage

client = (
    SeedrClientBuilder()
    .with_v2_token("access-token")
    .with_refresh_token("refresh-token", client_id="seedr_chrome")
    .on_token_refresh(save_token)
    .with_token_storage(FileTokenStorage(".seedr_token.json"))
    .with_timeout(120.0)
    .build()
)
```

### 8. Long-lived Session

```python
from seedr_api import SeedrSession
from seedr_api.core.token_storage import FileTokenStorage

storage = FileTokenStorage(".seedr_session.json")

# First run: logs in; subsequent runs: loads saved token
session = await SeedrSession.load_or_create(
    storage,
    username="user@example.com",
    password="password",
)

async with session.client as client:
    root = await client.filesystem.list_root_contents()
```

### 9. Anonymous (no token yet)

```python
client = SeedrClient.anonymous()
code = await client.auth.request_device_code("seedr_xbmc")
```

### 10. Custom Timeout

```python
client = SeedrClient.from_token("access-token", timeout=120.0)
```

---

## API Reference

### `client.auth` — AuthResource

| Method | Description |
|--------|-------------|
| `request_device_code(client_id)` | Start the device code flow |
| `poll_device_token(client_id, device_code, interval=5, max_wait=300)` | Poll until user approves |
| `refresh_token(refresh_token, client_id)` | Exchange refresh token for new access token |

### `client.account` — AccountResource

| Method | V1 | V2 | Description |
|--------|:--:|:--:|-------------|
| `get_settings()` | ✓ | ✓ | Account settings, user info, wishlist |
| `get_quota()` | ✓ | ✓ | Storage + bandwidth usage |
| `get_info()` | ✗ | ✓ | Detailed account info, features, subscription |
| `get_devices()` | ✓ | ✗ | Connected OAuth devices |
| `list_wishlist()` | ✓ | ✓ | List wishlist items |
| `delete_wishlist_item(item_id)` | ✓ | ✓ | Remove a wishlist item |

### `client.filesystem` — FilesystemResource

| Method | V1 | V2 | Description |
|--------|:--:|:--:|-------------|
| `list_root_contents()` | ✓ | ✓ | List root folder |
| `list_folder_contents(folder_id)` | ✓ | ✓ | List a folder |
| `get_folder(folder_id)` | ✗ | ✓ | Folder metadata |
| `get_file(file_id)` | ✗ | ✓ | File metadata |
| `create_folder(name)` | ✓ | ✓ | Create a new folder |
| `rename_folder(folder_id, new_name)` | ✓ | ✓ | Rename a folder |
| `rename_file(file_id, new_name)` | ✓ | ✓ | Rename a file |
| `delete_folder(folder_id)` | ✓ | ✓ | Delete a folder |
| `delete_file(file_id)` | ✓ | ✓ | Delete a file |

### `client.tasks` — TasksResource

| Method | V1 | V2 | Description |
|--------|:--:|:--:|-------------|
| `list()` | ✗ | ✓ | List active tasks |
| `add_magnet(magnet, folder_id=0)` | ✓ | ✓ | Add torrent from magnet link |
| `add_wishlist(wishlist_id)` | ✓ | ✓ | Add a wishlist item as a task |

### `client.downloads` — DownloadsResource

| Method | V1 | V2 | Description |
|--------|:--:|:--:|-------------|
| `get_download_url(file_id)` | ✓ | ✓ | Temporary download URL |
| `init_archive(uuid, folder_id, items)` | ✗ | ✓ | Create ZIP archive |

### `client.presentations` — PresentationsResource (V2 only)

| Method | Description |
|--------|-------------|
| `get_folder_presentations(folder_id)` | HLS stream + thumbnail URLs for all files in a folder |

### `client.subtitles` — SubtitlesResource (V2 only)

| Method | Description |
|--------|-------------|
| `list_subtitles(file_id)` | List available subtitles for a file |

### `client.search` — SearchResource

| Method | V1 | V2 | Description |
|--------|:--:|:--:|-------------|
| `search(query)` | ✓ | ✓ | Search your Seedr library |

---

## Models

### V1 Models — strict

Located in `seedr_api.models.v1.*`. Fields are **required** and match what the stable V1 API always returns. If a required field is missing, a `SeedrError` is raised at the adapter level — not a raw `ValidationError`.

```python
from seedr_api.models.v1.auth import V1TokenResponse, V1DeviceCode
from seedr_api.models.v1.account import V1AccountSettings, V1MemoryBandwidth, V1Device
from seedr_api.models.v1.filesystem import V1FolderContents, V1FolderItem, V1FileItem
from seedr_api.models.v1.tasks import V1FetchFileResult, V1SearchResult
```

Key V1 models:

| Model | Key Fields |
|-------|-----------|
| `V1TokenResponse` | `access_token`, `expires_in`, `token_type`, `refresh_token` |
| `V1DeviceCode` | `device_code`, `user_code`, `verification_url`, `interval`, `expires_in` |
| `V1AccountSettings` | `settings`, `account` (`user_id`, `email`, `space_used`, `space_max`, `wishlist`) |
| `V1MemoryBandwidth` | `space_used`, `space_max`, `bandwidth_used`, `bandwidth_max`, `is_premium` |
| `V1Device` | `client_id`, `client_name`, `device_code`, `tk` |
| `V1FolderContents` | `id`, `path`, `size`, `parent`, `folders`, `files`, `torrents` |
| `V1FolderItem` | `id`, `path`, `size`, `last_update`, `name`, `fullname` |
| `V1FileItem` | `id`, `name`, `size`, `hash`, `folder_id`, `is_video`, `is_audio`, `thumb` |
| `V1FetchFileResult` | `url`, `name`, `success` |
| `V1SearchResult` | `folders`, `files`, `path` |

### V2 Models — lenient

Located in `seedr_api.models.v2.*`. **All fields are `Optional[T] = None`** because V2 is alpha and shapes may change without notice. Your code will never crash due to a missing field.

```python
from seedr_api.models.v2.filesystem import V2FolderContents, V2FileInfo
from seedr_api.models.v2.account import V2AccountSettings, V2Quota, V2AccountInfo
from seedr_api.models.v2.tasks import V2Task, V2AddTaskResult
from seedr_api.models.v2.downloads import V2DownloadURL, V2ArchiveInit
from seedr_api.models.v2.presentations import V2FolderPresentations
from seedr_api.models.v2.subtitles import V2SubtitlesList
```

> **Always guard V2 fields before use:**
> ```python
> info = await client.filesystem.get_file(file_id)
> if info.name is not None:
>     print(info.name)
> ```

---

## Error Handling

```python
from seedr_api.exceptions import (
    SeedrError,             # base — catch-all
    AuthenticationError,    # 401 / access denied
    TokenExpiredError,      # token expired (subclass of AuthenticationError)
    ForbiddenError,         # 403
    NotFoundError,          # 404
    InsufficientSpaceError, # 413 — not enough space; torrent auto-added to wishlist
    RateLimitError,         # 429 — includes .retry_after (seconds)
    ServerError,            # 5xx
    APIError,               # other API-level errors
)
```

```python
from seedr_api.exceptions import InsufficientSpaceError, RateLimitError

try:
    task = await client.tasks.add_magnet("magnet:?xt=...")
except InsufficientSpaceError as e:
    print(f"No space — auto-added to wishlist: {e.wishlist_item}")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except NotFoundError:
    print("File or folder not found")
```

---

## Token Storage

```python
from seedr_api.core.token_storage import MemoryTokenStorage, FileTokenStorage

storage = MemoryTokenStorage()                          # in-memory (lost on restart)
storage = FileTokenStorage("/home/user/.seedr.json")   # persistent JSON file
```

Custom storage — implement the protocol:

```python
from seedr_api.core.token import Token

class RedisTokenStorage:
    async def save(self, token: Token) -> None:
        await redis.set("seedr_token", token.to_json())

    async def load(self) -> Token | None:
        data = await redis.get("seedr_token")
        return Token.from_json(data) if data else None
```

---

## V1 vs V2 Feature Matrix

| Feature | V1 | V2 |
|---------|:--:|:--:|
| Password login | ✓ | ✓ |
| Device code auth | ✓ | ✓ |
| Auto token refresh | ✓ | ✓ |
| List / browse folders | ✓ | ✓ |
| Create / rename / delete folder | ✓ | ✓ |
| Rename / delete file | ✓ | ✓ |
| Add torrent (magnet) | ✓ | ✓ |
| List active tasks | ✗ | ✓ |
| Get download URL | ✓ | ✓ |
| Archive (folder ZIP) | ✗ | ✓ |
| Search files | ✓ | ✓ |
| Subtitles | ✗ | ✓ |
| Presentations (HLS / thumbnails) | ✗ | ✓ |
| Account settings + quota | ✓ | ✓ |
| Detailed account info | ✗ | ✓ |
| **Connected devices** | ✓ | ✗ |
| Wishlist management | ✓ | ✓ |
| **Strict response models** | ✓ | ✗ |

---

## Architecture

```
SeedrClient  ·  SeedrSession  ·  SeedrClientBuilder
        │
        ▼
  Resources (auth, filesystem, tasks, downloads, …)
        │
        ▼
  Adapters
    ├── V1Adapter  →  www.seedr.cc/oauth_test/resource.php
    ├── V2Adapter  →  v2.seedr.cc/api/v0.1/p/
    └── AutoAdapter  →  routes per method (prefers V2)
        │
        ▼
  core/http.py (AsyncHTTPClient — aiohttp)
  core/token.py + core/token_storage.py
```

- **V1Adapter** — POSTs to `resource.php` with `func=` dispatch. Returns strict `models/v1/` models.
- **V2Adapter** — REST calls with OAuth Bearer header. Returns lenient `models/v2/` models (all Optional).
- **AutoAdapter** — Wraps both; routes each method to the preferred version. Use `prefer_v1()` / `prefer_v2()` on the builder.

---

## Development

```bash
pip install -e ".[dev]"
pytest                            # run tests
pytest --cov=seedr_api            # with coverage
ruff check src/ tests/            # lint
ruff format src/ tests/           # format
mypy src/                         # type check
```

---

## License

MIT — see [LICENSE](LICENSE)
