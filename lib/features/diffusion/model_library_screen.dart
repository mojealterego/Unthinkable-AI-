import 'native_engine_bridge.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'model_importer.dart';
import 'model_registry.dart';
import 'model_manifest.dart';

/// Adapted from ODYN-Diffusion-Android model_library_screen.dart.
/// Real import to app-private storage; no unsupported image-generation claims.
class ModelLibraryScreen extends StatefulWidget {
  const ModelLibraryScreen({super.key});
  @override State<ModelLibraryScreen> createState() => _ModelLibraryScreenState();
}

class _ModelLibraryScreenState extends State<ModelLibraryScreen> {
  ModelRegistry? registry;
  ModelImporter? importer;
  List<ModelManifest> models = const [];
  bool busy = false;
  bool? nativeAvailable;

  Future<void> _checkNative() async {
    if (busy) return;
    setState(() => busy = true);
    try {
      final available = await NativeEngineBridge().isAvailable();
      if (mounted) setState(() => nativeAvailable = available);
    } on Object {
      if (mounted) setState(() => nativeAvailable = false);
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;
    setState(() {
      registry = ModelRegistry(prefs);
      importer = ModelImporter(registry!);
      models = registry!.list();
    });
  }

  Future<void> _import() async {
    if (busy || importer == null) return;
    setState(() => busy = true);
    try {
      final model = await importer!.pickAndImport();
      if (!mounted) return;
      setState(() => models = registry!.list());
      if (model != null) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Model zapisany w pamięci aplikacji.')),
      );
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Import nieudany: $error')),
      );
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> _verify(ModelManifest model) async {
    if (busy || importer == null) return;
    setState(() => busy = true);
    try {
      final ok = await importer!.verifyIntegrity(model);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(ok ? 'SHA-256: plik modelu jest zgodny.'
                                  : 'SHA-256: brak sumy kontrolnej lub plik uszkodzony.')),
      );
    } on Object {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Nie udało się zweryfikować modelu.')),
      );
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> _remove(ModelManifest model) async {
    if (busy || importer == null) return;
    setState(() => busy = true);
    try {
      await importer!.remove(model);
      if (mounted) setState(() => models = registry!.list());
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Nie można usunąć modelu: $error')),
      );
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Biblioteka modeli ODYN')),
    body: ListView(padding: const EdgeInsets.all(16), children: [
      const Text('Import GGUF lub safetensors i zapis metadanych. '
        'Silnik natywnej generacji obrazu/wideo nie jest jeszcze podłączony.'),
      const SizedBox(height: 14),
      OutlinedButton(
        key: const Key('check_native_engine'),
        onPressed: busy ? null : _checkNative,
        child: const Text('Sprawdź natywny silnik inferencji'),
      ),
      if (nativeAvailable != null)
        Text(nativeAvailable!
          ? 'Silnik natywny zgłasza gotowość (wymaga testu urządzenia).'
          : 'Brak silnika natywnego. Nie jest dostępne lokalne generowanie.'),
      const SizedBox(height: 14),
      FilledButton.icon(
        key: const Key('import_model'),
        onPressed: busy || importer == null ? null : _import,
        icon: const Icon(Icons.file_open),
        label: Text(busy ? 'Importowanie…' : 'Importuj model z urządzenia'),
      ),
      const SizedBox(height: 16),
      if (models.isEmpty) const Text('Brak zaimportowanych modeli'),
      for (final model in models)
        ListTile(
          title: Text(model.displayName),
          subtitle: Text('${model.format.name} • ${model.modelPath}'),
          trailing: Row(mainAxisSize: MainAxisSize.min, children: [
            IconButton(
              tooltip: 'Zweryfikuj SHA-256',
              onPressed: busy ? null : () => _verify(model),
              icon: const Icon(Icons.verified_outlined),
            ),
            IconButton(
              tooltip: 'Usuń model',
              onPressed: busy ? null : () => _remove(model),
              icon: const Icon(Icons.delete_outline),
            ),
          ]),
        ),
    ]),
  );
}
