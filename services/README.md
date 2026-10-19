# Backend modules imported from the three user-specified repositories

Sources copied or adapted:
- StudioSync/Cinema from `mojealterego/Agentic-Cinema-The-Blockbuster-Hackathon` (`core/models.py`, `agents/orchestrator.py`, `services/demo_data.py`). The upstream README labels it Apache-2.0; standalone LICENSE still needs checking.
- Consent/creative orchestration from `mojealterego/Android-AI-Studio` (`backend/app/consent_core.py`, `backend/app/omni_orchestrator.py`). No standalone LICENSE found in initial repository tree; source transfer authorized by repository owner.
- ODYN-Diffusion Android code integrated directly in Flutter `lib/features/diffusion/` with file picker / metadata registry.

Modifications: relocated imports to `services.cinema`; corrected a demo provenance entry that was incorrectly labelled retrieved MCP data; added secured FastAPI gateway, offline tests and CI.

Start service (requires explicit API_KEY and a secured deployment):
`python -m pip install "fastapi>=0.116,<1" "pydantic>=2.11,<3" uvicorn`
`API_KEY="<secret>" uvicorn services.gateway.app:app --host 127.0.0.1 --port 8081`

Endpoints:
- `GET /health`: probe only.
- `POST /api/omni/orchestrator/plan`: Bearer API_KEY required; prepares plan, does not create media.
- `POST /api/cinema/incident`: Bearer API_KEY required; demo produces explicitly synthetic examples. Live ADK mode is not connected to a runner.

These are working application/service components, not completed image/video GPU generation. Flutter-to-backend planning integration is now implemented in `lib/features/video/production_api.dart`, but no public secured deployment or GPU backend is claimed. Grant checks provided by `consent_core` must be explicitly enforced before *every* state-changing endpoint. Requires TLS termination, identity, abuse limits, audit persistence and secret manager before exposure.

New endpoint: `POST /api/cinema/projects/plan` accepts the exact Flutter shotlist JSON, returns 18 crew planning roles, precise starts/ends and pending approvals. See `services/gateway/DEPLOY.md` for isolated Docker runtime and constraints.
