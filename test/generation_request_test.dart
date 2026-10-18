import 'package:flutter_test/flutter_test.dart';
import 'package:unthinkable_ai/features/diffusion/generation_engine.dart';
import 'package:unthinkable_ai/features/diffusion/model_manifest.dart';

void main() {
  const imageModel = ModelManifest(
    id: 'sdxl',
    displayName: 'SDXL',
    format: ModelFormat.gguf,
    capabilities: {ModelCapability.image},
    modelPath: '/models/sdxl.gguf',
  );

  test('valid image request', () {
    expect(const GenerationRequest(prompt: 'mountain', model: imageModel).validate(), isEmpty);
  });

  test('reject video for image-only model', () {
    expect(const GenerationRequest(prompt: 'mountain', model: imageModel, frames: 17)
        .validate(), contains('model_does_not_support_video'));
  });

  test('reject malformed sha256', () {
    const model = ModelManifest(
      id: 'invalid', displayName: 'Invalid', format: ModelFormat.gguf,
      capabilities: {ModelCapability.image}, modelPath: '/models/invalid.gguf',
      sha256: '1234',
    );
    expect(model.validate(), contains('invalid_sha256'));
  });

  test('engine refuses to pretend inference succeeded', () async {
    final engine = UnavailableNativeEngine();
    expect(await engine.isAvailable(), isFalse);
    expect(
      engine.generate(const GenerationRequest(prompt: 'test', model: imageModel)),
      throwsUnsupportedError,
    );
  });
}
