# Unthinkable AI — Reference Architecture v0.1 (PROPOSAL)

## Evidence states

**Observed:** source documents discuss `portable_ai_flutter`, `llamadart` and `llama.cpp` integration. No original APK or intact Dart source tree is present in the current checked-in repository. Code blocks in PDF/DOCX are candidates for independent clean-room review, not proofs of a working app.

**Verified so far:** `requirements/requirements.csv` tracks 339 requirement IDs. `tools/validate_requirements.py` passed GitHub Actions run 39158265987. Flutter code in `lib/main.dart` exposes a searchable **specification catalog** and no actual inference service yet.

**Unverified:** device inference speed, compatibility of Wan models/VAE, 123-minute NLE, multi-agent self-upgrades, always-on workers, user billing, SIP/PSTN activation, Tor browser isolation and formal math solver quality.

## Layered boundaries

```text
Flutter Android (+ optional desktop/web)
    │ Dart UI, Android OS permission adapters, vault UX
    │ FFI bindings, HTTPS authenticated service APIs
    ▼
Rust local core ─────── Model runtime adapters (llama.cpp / GGUF)
    │                    Native image/video model inference
    │                    Hardware + local cache/budget policies
    │
    ├─ Jobs / DGM policy / safe tool execution
    ├─ Zenoh/IPC adapters where measured benefit exists
    └─ Authenticated backend gateway (user grants, quotas)
             │
             ├─ Research & math jobs ── bibliographic provenance / solvers
             ├─ Media workers ──────── GPU pools / timeline renderer
             ├─ Builders ───────────── isolated editors / game engines
             ├─ Phone/communication ─ provider-provisioned numbers/E2EE
             ├─ Marketplace ────────── catalog, moderation, entitlements
             └─ Billing ────────────── licensed PSP, audited webhooks
```

The local private owner vault is a separately authorized security domain. Its SFTP/SMB/Google Drive/DB connections never inherit marketplace plugin credentials. The user-facing Tor mode requires a distinct browser profile, proxy leak tests and no claim of guaranteed anonymity.

## Proposed monorepo ownership

| Location | Planned role | Current state |
|---|---|---|
| `lib/`, `test/`, `pubspec.yaml` | Mobile UI and navigation | Prototype |
| `native/ffi/`, `crates/local-runtime/` | Rust/C++ local model runtime | Not implemented |
| `crates/model-router/` | Model descriptors, scheduling, compatibility | Not implemented |
| `services/gateway/` | Identity, scoped sessions, API auth | Not implemented |
| `services/job-scheduler/` | GPU jobs, cost/budget, isolation | Not implemented |
| `services/media/`, `services/nle/` | Image, video, audio and timeline tools | Not implemented |
| `services/builders/` | IDE, apps, games, agents and sandbox | Not implemented |
| `services/marketplace/`, `services/billing/` | Merchants, payments, subscriptions | Not implemented |
| `agents/github-engineer/` | Audited proposals, CI evidence, gated DGM | Not implemented |
| `agents/film-crew/`, `agents/mathematics/` | Crew / mathematical research | Not implemented |
| `infra/` | IBM/other cloud provisioning and monitoring | Not implemented |
| `requirements/`, `docs/` | Source traceability, ADRs and research prompt | Initial files created |

## Math and operations gates

- Do not assume zero-copy across process/network boundaries; benchmark Rust/Dart FFI memory lifetime, thread safety and IPC paths.
- Speculative decoding must preserve the target distribution and include compatible tokenizers, independent caches unless proven otherwise, and residual sampling.
- DGM must be an evaluated **propose → test → independent review → approve → deploy → monitor → rollback** state machine. No hidden unreviewed privilege escalation or automatic release.
- "Active inference", HDC and Nash formulations are optional research hypotheses until benchmarked versus simpler baselines; mathematical notation alone is not an implementation.
- For model checkpoint downloads, verify provenance, checksum, format, license, malicious archive paths, memory footprint and loader/API compatibility.
- Film >=123 minutes is a non-linear **timeline and segmented export** goal. Single-shot generative model length is separately constrained by GPU capacity and checkpoint.
- An arbitrary custom alias can exist internally. Calls to real public telephone numbers use operator-allocated, verified provisionable inventory.

## Priority and next evidence

P0: exact source-page traceability, Flutter debug APK, secure secrets and consent, native Flutter↔Rust build, model registry with one real runnable GGUF. Then model slots, media jobs/NLE, builder contracts, continuous engineer and audited billing. Every increment must add target file paths and runnable acceptance evidence to the requirement register. See `docs/DEEP_RESEARCH_MASTER_PROMPT.md`.
