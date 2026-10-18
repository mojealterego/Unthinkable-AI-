import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:unthinkable_ai/features/diffusion/model_manifest.dart';
import 'package:unthinkable_ai/features/diffusion/model_registry.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => SharedPreferences.setMockInitialValues({}));

  const model = ModelManifest(
    id: 'sd15',
    displayName: 'Stable Diffusion 1.5',
    format: ModelFormat.safetensors,
    capabilities: {ModelCapability.image},
    modelPath: '/models/sd15.safetensors',
  );

  test('persists and restores model metadata', () async {
    final prefs = await SharedPreferences.getInstance();
    final registry = ModelRegistry(prefs);
    await registry.add(model);
    final restored = ModelRegistry(prefs).list();
    expect(restored, hasLength(1));
    expect(restored.single.displayName, 'Stable Diffusion 1.5');
    expect(restored.single.capabilities, {ModelCapability.image});
  });

  test('upsert avoids duplicate model ids', () async {
    final prefs = await SharedPreferences.getInstance();
    final registry = ModelRegistry(prefs);
    await registry.add(model);
    await registry.add(model);
    expect(registry.list(), hasLength(1));
  });

  test('removes registered model', () async {
    final prefs = await SharedPreferences.getInstance();
    final registry = ModelRegistry(prefs);
    await registry.add(model);
    await registry.remove('sd15');
    expect(registry.list(), isEmpty);
  });

  test('rejects invalid metadata', () async {
    final prefs = await SharedPreferences.getInstance();
    final registry = ModelRegistry(prefs);
    await expectLater(
      registry.add(const ModelManifest(
        id: '',
        displayName: 'invalid',
        format: ModelFormat.gguf,
        capabilities: {ModelCapability.image},
        modelPath: '/models/invalid.gguf',
      )),
      throwsArgumentError,
    );
  });

  test('ignores corrupted stored JSON without crashing', () async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(ModelRegistry.storageKey, '{not json');
    expect(ModelRegistry(prefs).list(), isEmpty);
  });
}
