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
