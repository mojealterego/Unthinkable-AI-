# UNTHINKABLE AI

> Status: repository bootstrap / specification-first. The repository now contains a **Flutter module-catalog prototype** and a tested requirements-integrity workflow; it is **not** a completed AI application. No APK/AAB, backend, GPU pipeline, or continuous DGM agent has been verified yet.

## Product goal

Android-first AI platform with local GGUF inference and hybrid cloud compute. The intended system includes voice chat, multimodal generation, a professional film editor, Code/NoCode app/game/agent builders, Deep Research, a permissioned DGM/RSI improvement loop, communications, an owner-only research workspace, and a digital marketplace. **All requirements are tracked individually; none is considered implemented solely because a PDF describes it.**

## Architecture direction (proposed; not yet benchmarked)

- **Android/UI:** Flutter/Dart; Polish-default internationalization; native Android permissions and services; asset-driven Santa Muerte branding.
- **Native runtime:** Rust for policy, jobs and orchestration; C++ llama.cpp integration through FFI; keep binaries and memory ownership explicit.
- **Model adapters:** GGUF/Hugging Face; image and video model manifests with checkpoint, tokenizer/encoder, VAE and sampler compatibility, local GPU/CPU or cloud backends.
- **Compute backend:** authenticated job queue, object storage, ephemeral workers, payment entitlements, model/provider registry, observability and budgets.
- **Extension layer:** MCP adapters plus independently versioned plugins, skills, tools and sandboxed agent packages; no untrusted code with unrestricted host privileges.
- **Creative pipelines:** shot-based video generation and editor timeline with long-duration segmented render, music/voice, character reference management, game/app authoring.
- **Research:** citations, persistent source retrieval, reproducible experiments, solver integration (Lean/Coq/Z3), calibrated uncertainty, separate owner-only workspace.
- **Security:** owner vault; Android Keystore; encrypted one-time rooms; consented virtual telephone aliasing using allocated provider numbers; Tor isolation for privacy with no anonymity guarantees.

## Source provenance

Core inputs comprise the user's detailed feature specification and six supplied reference documents about DGM, agent taxonomy, orchestration, AI/IDE expansion, and Unthinkable AI architecture. APK-derived *observations*, prose *designs*, *illustrative code*, and *compiled/tested source* are **different evidence classes**. The evidence matrix must preserve this distinction.

## Implementation governance

1. Each requirement has a stable ID, source, acceptance test, target component and verified status.
2. Do not replace source evidence with unsupported guarantees (e.g. always <1 ms latency, perfect long-form actor continuity, uncensored models being unrestricted on every distribution channel).
3. DGM/RSI can propose/test patches continuously, but publishing an Android update or writing critical code requires policy gates, independent checks and rollback.
4. The target branch is `main`; no new branches are created by this bootstrap.
5. CI must actually compile/test the checked-out code; missing secrets, unavailable GPU infrastructure and absent APKs remain BLOCKED, not DONE.

## Completed repository bootstrap (evidence)

- `requirements/requirements.csv`: 339 individually tracked requirements in 27 source-derived domains; per-item page citations still pending.
- `docs/SOURCE_AUDIT.md`: source provenance and uncertainty ledger.
- `docs/DEEP_RESEARCH_MASTER_PROMPT.md`: engineering directive with full source coverage.
- `tools/validate_requirements.py`, `tests/test_requirements.py`: integrity validator and six unit tests.
- `.github/workflows/spec-check.yml`: first successful GitHub Actions validation: https://github.com/mojealterego/Unthinkable-AI-/actions/runs/39158265987
- `lib/main.dart`, `pubspec.yaml`, `test/widget_test.dart`: Flutter/Dart navigable Polish feature-catalog prototype; **not** implemented engines.
- `.github/workflows/flutter-smoke.yml`: Android debug APK smoke build, results must be checked individually.

## Next deliverables

- Page-accurate `requirements/traceability.csv` and decisions log.
- Versioned `docs/ARCHITECTURE.md` with components, APIs, secrets and deployment boundaries.
- Committed native Android project and version-pinned release toolchain.
- `crates/`, `services/`, `agents/`, `infra/`: real feature implementations and tests.

## Truthful current status

**Implemented:** repository bootstrap, requirements validation, Flutter module navigation prototype. **Verified:** the requirements-validation CI run above. **Unverified/incomplete:** Android smoke run until its conclusion, all actual AI engines, billing, media pipelines and deployments. Feature implementations, test evidence, APK/AAB builds and run IDs are separate milestones.
