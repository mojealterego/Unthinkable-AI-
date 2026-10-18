import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'model_manifest.dart';

/// Persistent metadata only. This does not copy or verify model files.
class ModelRegistry {
  ModelRegistry(this.preferences);
  final SharedPreferences preferences;
  static const storageKey = 'odyn.models.v1';

  List<ModelManifest> list() {
    final raw = preferences.getString(storageKey);
    if (raw == null || raw.isEmpty) return const [];
    try {
      final decoded = jsonDecode(raw);
      if (decoded is! List) return const [];
      return decoded.map((value) => _fromJson(value)).toList(growable: false);
    } on FormatException {
      return const [];
    } on TypeError {
      return const [];
    } on ArgumentError {
      return const [];
    }
  }

  Future<void> add(ModelManifest model) async {
    final errors = model.validate();
    if (errors.isNotEmpty) throw ArgumentError(errors.join(', '));
    final current = list().where((item) => item.id != model.id).toList();
    current.add(model);
    await _save(current);
  }

  Future<void> remove(String id) async {
    await _save(list().where((item) => item.id != id).toList());
  }

  Future<void> _save(List<ModelManifest> models) async {
    final encoded = jsonEncode(models.map(_toJson).toList());
    if (!await preferences.setString(storageKey, encoded)) {
      throw StateError('Unable to persist model registry');
    }
  }

  static Map<String, dynamic> _toJson(ModelManifest model) => {
    'id': model.id,
    'displayName': model.displayName,
    'format': model.format.name,
    'capabilities': model.capabilities.map((c) => c.name).toList(),
    'modelPath': model.modelPath,
    'vaePath': model.vaePath,
    'textEncoderPath': model.textEncoderPath,
    'sha256': model.sha256,
  };

  static ModelManifest _fromJson(dynamic data) {
    if (data is! Map<String, dynamic>) throw const FormatException('Invalid model');
    final capabilities = (data['capabilities'] as List<dynamic>)
        .map((name) => ModelCapability.values.byName(name as String)).toSet();
    final model = ModelManifest(
      id: data['id'] as String,
      displayName: data['displayName'] as String,
      format: ModelFormat.values.byName(data['format'] as String),
      capabilities: capabilities,
      modelPath: data['modelPath'] as String,
      vaePath: data['vaePath'] as String?,
      textEncoderPath: data['textEncoderPath'] as String?,
      sha256: data['sha256'] as String?,
    );
    if (model.validate().isNotEmpty) throw const FormatException('Invalid model');
    return model;
  }
}
