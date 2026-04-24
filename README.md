# seedr-api

[![PyPI](https://img.shields.io/pypi/v/seedr-api)](https://pypi.org/project/seedr-api/)
[![Python](https://img.shields.io/pypi/pyversions/seedr-api)](https://pypi.org/project/seedr-api/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/naveen/seedr-api/actions/workflows/ci.yml/badge.svg)](https://github.com/naveen/seedr-api/actions)

An **async** Python client library for the [Seedr](https://www.seedr.cc) API (v0.1).

## Features

- ✅ **Fully async** — built on `aiohttp`
- ✅ **Typed** — Pydantic v2 models, `py.typed`, `mypy --strict` compliant
- ✅ **Dual auth** — OAuth 2.0 tokens or email/password
- ✅ **Streaming downloads** — memory-efficient `AsyncGenerator` interface
- ✅ **Modular** — resources split by domain (filesystem, tasks, media, etc.)
- ✅ **PEP standards** — modern packaging with `hatchling`

## Installation

```bash
pip install seedr-api
```

## Quick Start

### With an OAuth access token
```python
import asyncio
from seedr_api import SeedrClient

async def main() -> None:
    async with SeedrClient.from_token("your-access-token") as client:
        # List root folder
        root = await client.filesystem.list_root_contents()
        print(root)

        # Add a magnet link
        task = await client.tasks.add_magnet("magnet:?xt=urn:btih:...")
        print(task)

        # Stream a file download
        async with client.downloads.stream_file(file_id=123) as stream:
            with open("output.mkv", "wb") as f:
                async for chunk in stream:
                    f.write(chunk)

asyncio.run(main())
```

### With email & password
```python
async with SeedrClient.from_credentials("you@example.com", "password") as client:
    user = await client.user.get()
    print(user.username, user.email)
```

## Resources

| Resource          | Accessor                   | Description                               |
|-------------------|----------------------------|-------------------------------------------|
| OAuth             | `client.auth`              | Token management, device code flow        |
| User              | `client.user`              | Profile, quota, settings                  |
| Filesystem        | `client.filesystem`        | Folders, files, batch operations          |
| Tasks             | `client.tasks`             | Torrent tasks (add, pause, resume, delete)|
| Downloads         | `client.downloads`         | Stream files, get download URLs           |
| Presentations     | `client.presentations`     | Streaming URLs, thumbnails, playlists     |
| Subtitles         | `client.subtitles`         | List, upload, search OpenSubtitles        |
| Search            | `client.search`            | Search library, scrape for magnets        |

## Device Code Flow (CLI apps)

```python
async with SeedrClient.from_credentials("", "") as client:
    device = await client.auth.request_device_code(client_id="your-client-id")
    print(f"Visit {device.verification_uri} and enter code: {device.user_code}")

    # Poll until user authorizes
    token = await client.auth.poll_device_token(
        client_id="your-client-id",
        device_code=device.device_code,
        interval=device.interval,
    )
    print(f"Access token: {token.access_token}")
```

## Error Handling

```python
from seedr_api.exceptions import NotFoundError, RateLimitError, AuthenticationError

try:
    await client.filesystem.get_file(file_id=999)
except NotFoundError:
    print("File not found")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except AuthenticationError:
    print("Invalid credentials or expired token")
```

## License

MIT © 2024
