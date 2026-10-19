# Production-planning API, exact durations and reference safety

The imported `Android-AI-Studio` Omni orchestrator now supports film timelines up to **12 hours**, including 123+ minutes, with remainder-aware exact distribution across scenes and rejected impossible durations. It does **not** synthesize or inspect video and does **not** guarantee reference locking: `continuity_source` is now `REFERENCE_REVIEW_REQUIRED`, replacing the misleading label `LOCKED_REFERENCE_GRAPH`.

The duration planner splits seconds among scenes; a true shot-aware algorithm must later import each stored FilmShot's actual time from the client. Converting an exact shotlist into a request that preserves per-shot duration requires a versioned endpoint and authentication/audit integration. No untrusted request can grant operational authority.

## Exact-shot API contract

`POST /api/cinema/projects/plan` accepts a `unthinkable-film-shotlist-v1` object directly from the Flutter film studio. Headers: `Authorization: Bearer <API_KEY>`, `Content-Type: application/json`. Request carries `title`, `masterPrompt`, and an ordered `shots` list (`id`, `name`, `durationSeconds`, `prompt`, `actorReference`, `mediaReference`, `approved`). Server rejects an empty list, duplicate IDs, invalid durations, and total duration over 12 hours.

Returns `unthinkable-production-plan-v1` with exact `start_seconds` and `end_seconds` for every scene, 18 planned cinematic crew steps, an explicit list of unapproved scene IDs, and `generated_video: false`. Access requires the configured API key. No models, jobs or real media generators are invoked by this endpoint. References are retained per shot and not claimed to be identity-locked.
