import 'dart:io';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:unthinkable_ai/features/diffusion/native_engine_bridge.dart';
import 'package:unthinkable_ai/features/diffusion/generation_engine.dart';
import 'package:unthinkable_ai/features/diffusion/model_manifest.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('odyn.diffusion/native_v1');
  final messenger = TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;

  GenerationRequest sample() => const GenerationRequest(
    prompt: 'landscape',
    model: ModelManifest(
      id:'sd15',displayName:'Model SD',format:ModelFormat.safetensors,
      capabilities:{ModelCapability.image},modelPath:'/models/example.safetensors',
    ),
  );

  tearDown(() => messenger.setMockMethodCallHandler(channel, null));

  test('No registered native engine refuses generation', () async {
    final bridge = NativeEngineBridge();
    expect(await bridge.isAvailable(), false);
    await expectLater(bridge.generate(sample()), throwsUnsupportedError);
  });

  test('A fake returned image path never counts as generated image', () async {
    messenger.setMockMethodCallHandler(channel, (call) async {
      if (call.method == 'isAvailable') return true;
      if (call.method == 'generate') return '/missing/unthinkable-output.png';
      return null;
    });
    await expectLater(NativeEngineBridge().generate(sample()), throwsStateError);
  });

  test('Native response must contain real PNG signature on disk', () async {
    final dir = await Directory.systemTemp.createTemp('native-image-validation-');
    try {
      final output = File('${dir.path}/output.png');
      await output.writeAsBytes([137,80,78,71,13,10,26,10,1,2,3]);
      messenger.setMockMethodCallHandler(channel, (call) async {
        if (call.method == 'isAvailable') return true;
        if (call.method == 'generate') {
          expect(call.arguments['prompt'], 'landscape');
          return output.path;
        }
        return null;
      });
      expect(await NativeEngineBridge().generate(sample()), output.path);
      await output.writeAsBytes([1,2,3,4,5,6,7,8,9]);
      await expectLater(NativeEngineBridge().generate(sample()), throwsStateError);
    } finally {
      await dir.delete(recursive:true);
    }
  });
}
