# Changelog

## v0.2.0 - 2026-11-27

- Completed Steps 1-8: modular FastAPI device API, validated request/response models, in-memory repository, service-level error handling, offline-transition alerts, documented OpenAPI contract, and automated service tests.
- Added Steps 9-13: environment-based MySQL configuration, SQLAlchemy session and ORM models, Alembic migrations for devices and alerts plus the optional device location field, and a MySQL repository behind the existing repository protocol.
- Kept in-memory storage as the default backend and added isolated SQLAlchemy repository tests for persistence behavior and duplicate-device handling.