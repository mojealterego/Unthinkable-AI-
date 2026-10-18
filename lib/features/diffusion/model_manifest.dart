enum ModelCapability { image, video, imageEdit }
enum ModelFormat { gguf, safetensors, qnn }

class ModelManifest {
  const ModelManifest({
    required this.id,
    required this.displayName,
    required this.format,
    required this.capabilities,
    required this.modelPath,
    this.vaePath,
    this.textEncoderPath,
    this.sha256,
  });

  final String id;
  final String displayName;
  final ModelFormat format;
  final Set<ModelCapability> capabilities;
  final String modelPath;
  final String? vaePath;
  final String? textEncoderPath;
  final String? sha256;

  List<String> validate() {
    final errors = <String>[];
    if (id.trim().isEmpty) errors.add('model_id_required');
    if (displayName.trim().isEmpty) errors.add('model_name_required');
    if (modelPath.trim().isEmpty) errors.add('model_path_required');
    if (capabilities.isEmpty) errors.add('capability_required');
    if (sha256 != null && !RegExp(r'^[a-fA-F0-9]{64}$').hasMatch(sha256!)) {
      errors.add('invalid_sha256');
    }
    return errors;
  }
}
