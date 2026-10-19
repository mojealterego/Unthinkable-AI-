# Build and verification

The initial Flutter app is a transparent *module-catalog prototype*, not the finished AI platform.

## Local environment

Install a compatible stable Flutter SDK and an Android SDK/JDK. The repository does not yet check in the generated native Android Gradle wrapper. Initialize it on a build host:

```sh
flutter create --project-name unthinkable_ai --platforms android .
flutter pub get
flutter analyze --no-fatal-infos
flutter test
flutter build apk --debug
```

Output on success: `build/app/outputs/flutter-apk/app-debug.apk`. The debug APK is **not** an AAB, a release-signed artifact, or proof of implementation of 339 features.

## CI evidence

- `.github/workflows/spec-check.yml`: validates source coverage and Python tests.
- `.github/workflows/flutter-smoke.yml`: installs Flutter, creates native Android project, analyzes Dart, runs widget tests, builds a debug APK, uploads it as an Actions artifact.
- Future delivery: pinned Flutter/Gradle version and committed native wrapper, SBOM, provenance signing, secure release keystore, app-store policies and E2E device tests.

## APK provenance

Source documents report decompilation of an earlier Flutter APK. Decompiled symbol names and illustrative code blocks do **not** reconstruct a compilable original Dart/Flutter source tree or transfer its license. Treat the APK as a reference and reverse-engineering research artifact. Require permission/licensing review and compare observed capabilities to new independent source code before reusing.

## Incremental verified functionality

- A local film shotlist planner provides scene timing, scene order, cast/media reference strings, master prompt, per-scene approval, local persistence and JSON clipboard import/export. **It is not a video renderer or a full NLE.**
- An HTTPS Chat Completions adapter provides text chat for an OpenAI-compatible provider after the user supplies a model ID and API key. The key stays in memory and is not saved to disk. Local GGUF inference is **not** implemented.
- An automated GitHub Actions CI monitor checks failing main-branch workflows every four hours and creates deduplicated incident issues. It is **not** an autonomous code-writing DGM.
- User directives (146), sourced proposal candidates (53) and the original 339-entry register are preserved separately. Passing the traceability validation does **not** mean the full application is implemented.

For actual build and test status inspect `.github/workflows/flutter-smoke.yml`, `.github/workflows/spec-check.yml` and `.github/workflows/traceability.yml`; do not infer an APK from a passing analysis-only job.

## Current native-model and cinema-planning additions

- `production_api.dart`: sends the full shotlist over HTTPS after explicit user request. Endpoint: `POST /api/cinema/projects/plan`. It enforces schema, scene order, duration and 18-role structure on the returned plan.
- `services/gateway/Dockerfile`: isolated container build with a non-root user. See `services/gateway/DEPLOY.md`; an externally reachable HTTPS endpoint is **not provisioned automatically**.
- `model_integrity.dart`: streaming SHA-256 of imported GGUF/safetensors and on-demand verification; existing imports without historical checksum are flagged unverified.
- `native_engine_bridge.dart`: ODYN MethodChannel `odyn.diffusion/native_v1` adapter. On the current Flutter-generated Android host, the method channel is absent and returns `isAvailable=false`. The native C++/JNI implementation and physical GPU benchmarks remain a separate release gate.
- The GitHub CI currently generates an Android host and adjusts its compileSdk and file_picker plugin to API 36. This temporary adjustment must be replaced by a committed, version-pinned Android project before release.

The latest debug APK validation is always visible in GitHub Actions; passing a previous run does not verify a new commit. Do not treat SHA validation of bytes as compatibility with any particular inference runtime.
