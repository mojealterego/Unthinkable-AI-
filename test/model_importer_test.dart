import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:unthinkable_ai/features/diffusion/model_importer.dart';
import 'package:unthinkable_ai/features/diffusion/model_registry.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('unsupported extension is rejected before filesystem access', () async {
    final prefs = await SharedPreferences.getInstance();
    final importer = ModelImporter(ModelRegistry(prefs));
    await expectLater(
      importer.importFile(File('/does/not/exist'), displayName: 'model.exe'),
      throwsFormatException,
    );
  });

  test('empty source is rejected without registering model', () async {
    final prefs = await SharedPreferences.getInstance();
    final importer = ModelImporter(ModelRegistry(prefs));
    final dir = await Directory.systemTemp.createTemp('odyn-model-test-');
    try {
      final file = File('${dir.path}/empty.gguf');
      await file.create();
      await expectLater(
        importer.importFile(file, displayName: 'empty.gguf'),
        throwsFileSystemException,
      );
      expect(ModelRegistry(prefs).list(), isEmpty);
    } finally {
      await dir.delete(recursive: true);
    }
  });
}
