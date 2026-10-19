# Production-planning API, exact durations and reference safety

The imported `Android-AI-Studio` Omni orchestrator now supports film timelines up to **12 hours**, including 123+ minutes, with remainder-aware exact distribution across scenes and rejected impossible durations. It does **not** synthesize or inspect video and does **not** guarantee reference locking: `continuity_source` is now `REFERENCE_REVIEW_REQUIRED`, replacing the misleading label `LOCKED_REFERENCE_GRAPH`.

The duration planner splits seconds among scenes; a true shot-aware algorithm must later import each stored FilmShot's actual time from the client. Converting an exact shotlist into a request that preserves per-shot duration requires a versioned endpoint and authentication/audit integration. No untrusted request can grant operational authority.
