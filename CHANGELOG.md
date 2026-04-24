# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-24

### Added
- Initial release of `seedr-api`.
- Async client (`SeedrClient`) built on `aiohttp`.
- Full coverage of Seedr API v0.1: OAuth, Filesystem, Tasks, Downloads,
  Presentations, Subtitles, Search, and User resources.
- Pydantic v2 typed response models.
- Streaming download support via `AsyncGenerator`.
- Dual auth: OAuth 2.0 access token and email/password (Basic Auth).
- Device Code OAuth flow for CLI/TV apps.
- Custom exception hierarchy mapped to HTTP status codes.
- `py.typed` marker for full `mypy --strict` compliance.
- GitHub Actions CI (ruff + mypy + pytest).
