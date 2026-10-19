# Durable VisionStory job ledger

Server-side SQLite ledger supports idempotent paid talking-avatar and AI-video requests.

Deployment configuration: VISIONSTORY_JOB_DB_PATH must be absolute and must reside on a durable private volume. For production set VISIONSTORY_REQUIRE_DURABLE_JOBS=1. Without this setting the legacy single-owner service may run without durable idempotency and must NOT be described as production ready.

Store behavior: each (namespace, client_request_id) has canonical SHA256 of submitted payload, state sending/ambiguous/submitted, video_id and timestamps. Matching, completed requests return the existing ID without a second POST. Concurrent or uncertain outcomes block retries with 409. No prompt/media/secret is persisted. There is no automatic paid retry.

Authenticated read-only GET /api/cinema/visionstory/jobs returns up to 200 records. Global gateway key is single owner. Do not expose it as a multi-user archive without per-user authorization, isolated media storage and tenant-aware database schema.

CI: tests/test_visionstory_jobs.py, verifying restart, transaction conflict, ambiguous timeout and reuse. Mock-only. A real VisionStory provider account and durable hosted SQLite volume are not configured by these tests.