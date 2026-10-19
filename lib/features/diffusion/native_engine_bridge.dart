import 'dart:io';
import 'package:flutter/services.dart';
import 'generation_engine.dart';

/// Channel contract from ODYN Diffusion Android. No native library is bundled
/// in the current APK; absence MUST be reported and never simulated as success.
class NativeEngineBridge implements GenerationEngine {
  NativeEngineBridge({MethodChannel? channel})
      : _channel = channel ?? const MethodChannel('odyn.diffusion/native_v1');
  final MethodChannel _channel;

  @override
  Future<bool> isAvailable() async {
    try {
      return await _channel.invokeMethod<bool>('isAvailable') ?? false;
    } on MissingPluginException {
      return false;
    } on PlatformException {
      return false;
    }
  }

  @override
  Future<String> generate(GenerationRequest request) async {
    final errors = request.validate();
    if (errors.isNotEmpty) throw ArgumentError(errors.join(', '));
    if (request.frames != 1) {
      throw UnsupportedError('Local video generation is not implemented');
    }
    if (!await isAvailable()) {
      throw UnsupportedError('Native diffusion engine is not installed');
    }
    final output = await _channel.invokeMethod<String>('generate', {
      'prompt': request.prompt,
      'modelPath': request.model.modelPath,
      'vaePath': request.model.vaePath,
      'textEncoderPath': request.model.textEncoderPath,
      'width': request.width,
      'height': request.height,
      'steps': request.steps,
      'frames': request.frames,
      'seed': request.seed,
    });
    if (output == null || output.isEmpty) {
      throw StateError('Native engine reported no output');
    }
    // Verify an actual nonempty PNG was created; a returned path alone is not a generation.
    final result = File(output);
    if (!await result.exists() || await result.length() < 8) {
      throw StateError('Native image does not exist or is incomplete');
    }
    final signature = <int>[137, 80, 78, 71, 13, 10, 26, 10];
    final header = await result.openRead(0, 8).first;
    if (header.length != signature.length) throw StateError('Image header missing');
    for (var i = 0; i < signature.length; i++) {
      if (header[i] != signature[i]) throw StateError('Native output is not a PNG');
    }
    return output;
  }

  @override
  Future<void> cancel() async {
    if (await isAvailable()) await _channel.invokeMethod<void>('cancel');
  }
}
