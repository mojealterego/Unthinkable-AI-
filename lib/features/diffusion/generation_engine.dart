import 'model_manifest.dart';

class GenerationRequest {
  const GenerationRequest({
    required this.prompt,
    required this.model,
    this.width = 512,
    this.height = 512,
    this.steps = 20,
    this.frames = 1,
    this.seed = -1,
  });
  final String prompt;
  final ModelManifest model;
  final int width;
  final int height;
  final int steps;
  final int frames;
  final int seed;

  List<String> validate() {
    final errors = <String>[...model.validate()];
    if (prompt.trim().isEmpty) errors.add('prompt_required');
    if (width < 64 || width > 2048 || width % 8 != 0) errors.add('invalid_width');
    if (height < 64 || height > 2048 || height % 8 != 0) errors.add('invalid_height');
    if (steps < 1 || steps > 150) errors.add('invalid_steps');
    if (frames < 1 || frames > 121) errors.add('invalid_frames');
    if (frames > 1 && !model.capabilities.contains(ModelCapability.video)) {
      errors.add('model_does_not_support_video');
    }
    if (frames == 1 && !model.capabilities.contains(ModelCapability.image)) {
      errors.add('model_does_not_support_image');
    }
    return errors;
  }
}

abstract interface class GenerationEngine {
  Future<bool> isAvailable();
  Future<String> generate(GenerationRequest request);
  Future<void> cancel();
}

class UnavailableNativeEngine implements GenerationEngine {
  @override
  Future<bool> isAvailable() async => false;
  @override
  Future<String> generate(GenerationRequest request) async {
    final errors = request.validate();
    if (errors.isNotEmpty) throw ArgumentError(errors.join(', '));
    throw UnsupportedError('Native inference engine is not installed');
  }
  @override
  Future<void> cancel() async {}
}
