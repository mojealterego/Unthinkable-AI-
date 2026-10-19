# Unthinkable Cinema API — isolated deployment

This service exposes **real** HTTP endpoints for film shot planning and roster generation. It does **not** run media inference or execute external production actions.

## Local Docker deployment

1. Define a new long random `API_KEY` in the environment of the server (not in GitHub or the Flutter source tree).
2. Build: `docker build -f services/gateway/Dockerfile -t unthinkable-cinema:local .`
3. Run on loopback only:
   `docker run --rm --read-only --cap-drop=ALL --security-opt=no-new-privileges --tmpfs /tmp -e API_KEY -p 127.0.0.1:8081:8081 unthinkable-cinema:local`
4. Verify `curl http://127.0.0.1:8081/health` reports `real_media_generation: false`.
5. Place an authenticated, rate-limited TLS reverse proxy in front of the container with a valid HTTPS certificate before connecting Android. The Flutter client refuses HTTP addresses.

Server routes:
- `POST /api/cinema/projects/plan`: ordered per-shot timeline, exact times, original actor/media references, 18 role plans and unresolved approvals. Requires Bearer API_KEY.
- `POST /api/cinema/crew`: separate 18-role role plan. Requires Bearer API_KEY.
- `POST /api/omni/orchestrator/plan`: planning route from Android AI Studio. Requires Bearer API_KEY.
- `POST /api/cinema/incident`: synthetic-only operational simulation, no real ClickHouse data without a configured runner. Requires Bearer API_KEY.

The container has no embedded model weights, no secret tokens baked into layers, and uses non-root user. Never enable a browser-exposed CORS wildcard, embed the API_KEY in the APK, or expose the HTTP container port publicly. An API key in memory is a prototype identity scheme and does not replace durable per-user identity, independent scoped grants, signed receipts, authz and rate limiting for production.

## Acceptance
Backend API CI checks HTTP authentication, a 123+ minute film, exact per-shot durations and approvals, 18-role roster, and rejected malformed input. Flutter CI checks that the mobile client sends exactly the saved shotlist and validates server replies. No inference or device install is claimed by these checks.
