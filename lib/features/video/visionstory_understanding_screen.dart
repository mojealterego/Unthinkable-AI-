import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'visionstory_gateway.dart';

/// Synchronous, potentially paid VisionStory JSON extraction.
/// The provider API key stays on the server; no automatic retries.
class VisionStoryUnderstandingScreen extends StatefulWidget {
  const VisionStoryUnderstandingScreen({
    super.key, this.gateway, this.initialServer = '', this.initialGatewayKey = '',
  });
  final VisionStoryGateway? gateway;
  final String initialServer;
  final String initialGatewayKey;

  @override
  State<VisionStoryUnderstandingScreen> createState() => _UnderstandingState();
}

class _UnderstandingState extends State<VisionStoryUnderstandingScreen> {
  late final VisionStoryGateway gateway;
  late final bool ownsGateway;
  late final TextEditingController host;
  late final TextEditingController accessKey;
  final assetIds = TextEditingController();
  final instruction = TextEditingController(
    text: 'Rozpoznaj temat i opisz główną scenę.',
  );
  final responseSchema = TextEditingController(text:
      '{"type":"object","properties":{"subject":{"type":"string"},'
      '"scene":{"type":"string"}},"required":["subject","scene"],'
      '"additionalProperties":false}');
  bool rights = false, costApproved = false, busy = false;
  Map<String, dynamic>? output;
  String? error;

  @override
  void initState() {
    super.initState();
    ownsGateway = widget.gateway == null;
    gateway = widget.gateway ?? VisionStoryGateway();
    host = TextEditingController(text: widget.initialServer);
    accessKey = TextEditingController(text: widget.initialGatewayKey);
  }

  @override
  void dispose() {
    host.dispose();
    accessKey.clear();
    accessKey.dispose();
    instruction.dispose();
    responseSchema.dispose();
    assetIds.dispose();
    if (ownsGateway) gateway.close();
    super.dispose();
  }

  Map<String, Object?> buildRequest() {
    final prompt = instruction.text.trim();
    if (prompt.isEmpty || prompt.length > 5000) {
      throw const FormatException('Polecenie musi mieć od 1 do 5000 znaków.');
    }
    final ids = assetIds.text
      .split(RegExp(r'[,\s;]+'))
      .map((x) => x.trim())
      .where((x) => x.isNotEmpty).toList();
    if (ids.isEmpty || ids.length > 8 || ids.toSet().length != ids.length) {
      throw const FormatException('Wymagane 1–8 różnych identyfikatorów zasobów.');
    }
    final idRule = RegExp(r'^[A-Za-z0-9_-]{3,160}$');
    if (ids.any((x) => !idRule.hasMatch(x))) {
      throw const FormatException('Użyj asset_id, nie adresu pliku ani lokalnej ścieżki.');
    }
    final decoded = jsonDecode(responseSchema.text);
    if (decoded is! Map<String, dynamic> ||
        decoded['type'] != 'object' ||
        decoded['properties'] is! Map ||
        (decoded['properties'] as Map).isEmpty) {
      throw const FormatException('Wymagany schemat JSON obiektu z właściwościami.');
    }
    if (utf8.encode(responseSchema.text).length > 20000) {
      throw const FormatException('Schemat JSON może mieć maksymalnie 20 KB.');
    }
    return {
      'prompt': prompt,
      'inputs': ids.map((x) => {'asset_id': x}).toList(),
      'schema': decoded,
      'confirmed_media_rights': true,
      'approved_for_paid_generation': true,
    };
  }

  Future<void> submit() async {
    if (busy) return;
    setState(() { error = null; output = null; });
    if (!rights || !costApproved) {
      setState(() => error = 'Potwierdź prawa do mediów i możliwy koszt.');
      return;
    }
    Map<String, Object?> request;
    try {
      request = buildRequest();
    } on FormatException catch (e) {
      if (mounted) setState(() => error = e.message);
      return;
    } on Object {
      if (mounted) setState(() => error = 'Niepoprawna składnia schematu JSON.');
      return;
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Potwierdzenie płatnej analizy'),
        content: const Text(
          'Wskazane media zostaną przekazane zewnętrznemu dostawcy. '
          'Operacja może zużyć kredyty i trwać do 180 sekund. '
          'Po przekroczeniu czasu nie wolno automatycznie ponawiać żądania.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Anuluj')),
          FilledButton(
            key: const Key('vs_understand_confirm'),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Zatwierdzam koszt')),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => busy = true);
    try {
      final response = await gateway.call(
        server: host.text,
        key: accessKey.text,
        path: 'media/understand',
        body: request,
      );
      if (response['output'] is! Map || response['usage'] is! Map ||
          response['cost_credit'] is! int) {
        throw const FormatException('Niekompletna odpowiedź VisionStory.');
      }
      if (mounted) setState(() => output = response);
    } on VisionStoryGatewayError catch (e) {
      if (mounted) setState(() =>
        error = e.message + ' Nie ponawiaj automatycznie płatnej analizy.');
    } on FormatException catch (e) {
      if (mounted) setState(() => error = e.message);
    } on Object {
      if (mounted) setState(() =>
        error = 'Nie potwierdzono wykonania; nie ponawiaj automatycznie.');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Widget field(String id, String label, TextEditingController controller,
      {int lines = 1, bool secret = false}) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 6),
    child: TextField(
      key: Key(id), controller: controller, maxLines: lines,
      obscureText: secret, autocorrect: !secret, enableSuggestions: !secret,
      decoration: InputDecoration(labelText: label,
        border: const OutlineInputBorder()),
    ),
  );

  @override
  Widget build(BuildContext context) {
    final result = output;
    return Scaffold(
      appBar: AppBar(title: const Text('VisionStory — Analiza mediów')),
      body: SafeArea(child: ListView(padding: const EdgeInsets.all(16),
        children: [
          const Text('Wynik JSON z 1–8 obrazów, nagrań lub filmów. '
            'Wybierz istniejące asset_id z biblioteki VisionStory. '
            'To analiza synchroniczna, a nie generowanie nowego filmu.'),
          const SizedBox(height: 12),
          field('vs_understand_host', 'Twój prywatny serwer HTTPS', host),
          field('vs_understand_key', 'Klucz gateway (niezapisany)', accessKey,
            secret: true),
          field('vs_understand_assets',
            'ID zasobów (1–8, oddzielone przecinkami)', assetIds, lines: 2),
          field('vs_understand_prompt', 'Polecenie analizy', instruction, lines: 3),
          field('vs_understand_schema', 'Schemat odpowiedzi JSON',
            responseSchema, lines: 7),
          CheckboxListTile(
            key: const Key('vs_understand_rights'), value: rights,
            onChanged: busy ? null :
              (v) => setState(() => rights = v ?? false),
            title: const Text('Mam prawa do przekazywanych materiałów')),
          CheckboxListTile(
            key: const Key('vs_understand_paid'), value: costApproved,
            onChanged: busy ? null :
              (v) => setState(() => costApproved = v ?? false),
            title: const Text('Akceptuję ewentualny koszt w kredytach')),
          FilledButton.icon(
            key: const Key('vs_understand_submit'), onPressed: busy ? null : submit,
            icon: const Icon(Icons.document_scanner_outlined),
            label: const Text('Rozpocznij analizę mediów')),
          if (busy) const LinearProgressIndicator(),
          if (error != null)
            Text(error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
          if (result != null) ...[
            const SizedBox(height: 12),
            Text('Wynik analizy', style: Theme.of(context).textTheme.titleLarge),
            Text('Koszt: ' + result['cost_credit'].toString() + ' kredytów'),
            Text('Zużycie: ' + jsonEncode(result['usage'])),
            SelectableText(
              const JsonEncoder.withIndent('  ').convert(result['output']),
              key: const Key('vs_understand_result')),
            TextButton.icon(
              onPressed: () => Clipboard.setData(ClipboardData(
                text: const JsonEncoder.withIndent('  ')
                    .convert(result['output']))),
              icon: const Icon(Icons.copy), label: const Text('Kopiuj JSON')),
          ],
        ],
      )),
    );
  }
}
