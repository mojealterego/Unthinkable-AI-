import 'dart:convert';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'visionstory_gateway.dart';
import 'visionstory_understanding_screen.dart';

/// Connected provider tools. Final artwork/UI will be provided by the owner.
/// Provider secrets never enter the app. All external uploads require consent.
class VisionStoryMediaToolsScreen extends StatefulWidget {
  const VisionStoryMediaToolsScreen({super.key, this.gateway});
  final VisionStoryGateway? gateway;
  @override
  State<VisionStoryMediaToolsScreen> createState() => _VisionStoryMediaToolsScreenState();
}

class _VisionStoryMediaToolsScreenState extends State<VisionStoryMediaToolsScreen> {
  late final VisionStoryGateway api;
  final host = TextEditingController();
  final key = TextEditingController();
  final model = TextEditingController();
  final prompt = TextEditingController();
  final asset = TextEditingController();
  final avatar = TextEditingController();
  final creditCap = TextEditingController(text: '5');
  final voicePreview = TextEditingController(text: 'Witaj w Unthinkable AI.');
  bool rights = false, consent = false, paid = false, busy = false;
  String? error, notice, filename, mime, kind;
  String? ratio, resolution;
  List<int>? bytes;
  Map<String, dynamic>? result, catalog, imageQuote;
  String? quotedImageParams;
  bool imageStateLoaded = false, imageAttempted = true;
  static const _imageAttemptKey = 'unthinkable.visionstory.image.paid.attempted';

  @override void initState() {
    super.initState();
    api = widget.gateway ?? VisionStoryGateway();
    _restoreImageAttempt();
  }

  Future<void> _restoreImageAttempt() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      if (mounted) setState(() {
        imageAttempted = prefs.getBool(_imageAttemptKey) ?? false;
        imageStateLoaded = true;
      });
    } on Object {
      if (mounted) setState(() {
        imageAttempted = true;
        imageStateLoaded = true;
        error = 'Nie odczytano historii płatnego obrazu. Ponowienie zablokowane.';
      });
    }
  }

  Future<void> _persistImageAttempt(bool attempted) async {
    final prefs = await SharedPreferences.getInstance();
    if (!await prefs.setBool(_imageAttemptKey, attempted)) {
      throw const FormatException('Nie można zapisać stanu płatnego zadania.');
    }
    if (mounted) setState(() => imageAttempted = attempted);
  }

  Future<void> startNewImage() async {
    final accepted = await showDialog<bool>(context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Nowa płatna generacja?'),
        content: const Text(
          'Jeżeli poprzednie żądanie miało timeout, mogło zostać naliczone. '
          'Sprawdź historię VisionStory przed zatwierdzeniem nowej generacji.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Anuluj')),
          FilledButton(onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Nowe zadanie')),
        ],
      ),
    );
    if (accepted != true) return;
    await run(() async { await _persistImageAttempt(false); });
    if (mounted) setState(() {
      imageQuote = null;
      quotedImageParams = null;
    });
  }

  @override void dispose() {
    for (final c in [host, key, model, prompt, asset, avatar, creditCap, voicePreview]) {
      c.dispose();
    }
    api.close();
    super.dispose();
  }

  Future<void> run(Future<void> Function() fn) async {
    if (busy) return;
    setState(() { busy = true; error = null; notice = null; });
    try {
      await fn();
    } on FormatException catch (e) {
      if (mounted) setState(() => error = e.message);
    } on VisionStoryGatewayError catch (e) {
      if (mounted) setState(() => error = e.message);
    } on Object {
      if (mounted) setState(() => error =
        'Nie udało się wykonać działania; nie ponawiaj automatycznie płatnej operacji.');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<Map<String, dynamic>> get(String route) =>
      api.call(server: host.text, key: key.text, path: route);
  Future<Map<String, dynamic>> post(String route, Map<String, Object?> data) =>
      api.call(server: host.text, key: key.text, path: route, body: data);

  Future<bool> approve(String title, {bool billable = false, bool person = false}) async {
    if (!rights || (person && !consent) || (billable && !paid)) {
      setState(() => error = 'Wymagane potwierdzenie praw, zgody osoby i ewentualnego kosztu.');
      return false;
    }
    if (!mounted) return false;
    return (await showDialog<bool>(context: context, builder: (context) =>
      AlertDialog(
        title: Text(title),
        content: Text(billable
          ? 'Operacja może naliczyć kredyty VisionStory. Potwierdzasz uruchomienie?'
          : 'Materiały zostaną przekazane zewnętrznemu dostawcy. Potwierdzasz?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false),
            child: const Text('Anuluj')),
          FilledButton(onPressed: () => Navigator.pop(context, true),
            child: const Text('Potwierdzam')),
        ],
      ))) ?? false;
  }

  Future<void> choose(String selectedKind) async {
    try {
      final extensions = selectedKind == 'image'
          ? ['png', 'jpg', 'jpeg', 'webp', 'heic']
          : ['mp3', 'wav', 'm4a'];
      final selection = await FilePicker.platform.pickFiles(
        type: FileType.custom, allowedExtensions: extensions, withData: true);
      if (selection == null || selection.files.isEmpty) return;
      final item = selection.files.single;
      if (item.bytes == null || item.bytes!.isEmpty || item.size > 8000000) {
        throw const FormatException('Plik musi mieć od 1 B do 8 MB.');
      }
      final mimeType = switch (item.extension?.toLowerCase()) {
        'png' => 'image/png',
        'jpg' || 'jpeg' => 'image/jpeg',
        'webp' => 'image/webp',
        'heic' => 'image/heic',
        'mp3' => 'audio/mpeg',
        'wav' => 'audio/wav',
        'm4a' => 'audio/m4a',
        _ => null,
      };
      if (mimeType == null) throw const FormatException('Nieobsługiwany format.');
      if (mounted) setState(() {
        filename = item.name;
        kind = selectedKind;
        mime = mimeType;
        bytes = item.bytes!;
      });
    } on Object {
      if (mounted) setState(() => error = 'Nie udało się odczytać pliku.');
    }
  }

  Map<String, Object?> inline(String expected) {
    if (kind != expected || bytes == null || mime == null) {
      throw const FormatException('Wybierz odpowiedni plik w tym module.');
    }
    return {'mime_type': mime!, 'data': base64Encode(bytes!)};
  }

  Future<void> upload() async {
    if (!await approve('Prześlij plik do VisionStory')) return;
    await run(() async {
      final response = await post('assets/upload', {
        'inline_data': inline(kind ?? ''),
        'confirmed_media_rights': true,
        'approved_external_upload': true,
      });
      if (mounted) setState(() {
        result = response;
        asset.text = (response['asset_id'] ?? '').toString();
        notice = 'Plik przesłany. Zachowaj ID zasobu.';
      });
    });
  }

  Future<void> makeAvatar() async {
    if (!await approve('Utwórz awatar z portretu', person: true)) return;
    await run(() async {
      final response = await post('avatars/create', {
        'inline_data': inline('image'),
        'confirmed_image_rights': true,
        'confirmed_subject_consent': true,
        'approved_external_upload': true,
      });
      if (mounted) setState(() {
        result = response;
        avatar.text = (response['avatar_id'] ?? '').toString();
        notice = 'Utworzono awatar. Możesz go wybrać w Studio Filmowym.';
      });
    });
  }

  Future<void> cloneVoice() async {
    if (!await approve('Klonuj głos za zgodą jego właściciela', person: true)) return;
    await run(() async {
      final response = await post('voices/clone', {
        'inline_data': inline('audio'),
        'preview_text': voicePreview.text.trim(),
        'confirmed_voice_owner_consent': true,
        'approved_external_upload': true,
      });
      if (mounted) setState(() { result = response; notice = 'Utworzono głos.'; });
    });
  }

  Future<void> frameAvatar() async {
    if (!await approve('Zmień kadrowanie własnego awatara')) return;
    await run(() async {
      final response = await post('avatars/framing', {
        'avatar_id': avatar.text.trim(),
        'aspect_ratio': ratio ?? '9:16',
        'zoom': 1.0, 'offset_x': 0.0, 'offset_y': 0.0,
        'confirmed_framing_change': true,
      });
      if (mounted) setState(() { result = response; notice = 'Zapisano kadrowanie.'; });
    });
  }

  Future<void> imageModels() => run(() async {
    final data = await get('models/image');
    if (mounted) setState(() { catalog = data; notice = 'Modele pobrane od dostawcy.'; });
  });

  Map<String, Object?> imageParameters() => {
    'model_id': model.text.trim(),
    'prompt': prompt.text.trim(),
    if (resolution != null) 'resolution': resolution,
    if (ratio != null) 'aspect_ratio': ratio,
    if (asset.text.trim().isNotEmpty)
      'refs': [{'asset_id': asset.text.trim()}],
  };

  Future<void> estimateImage() => run(() async {
    if (model.text.trim().isEmpty || prompt.text.trim().isEmpty) {
      throw const FormatException('Wybierz model i uzupełnij opis.');
    }
    final parameters = imageParameters();
    final estimate = await post('images/estimate', parameters);
    if (mounted) setState(() {
      imageQuote = estimate;
      quotedImageParams = jsonEncode(parameters);
      notice = 'Wycena z katalogu dostawcy. Nie wykonano generacji.';
    });
  });

  Future<void> images() async {
    if (!imageStateLoaded || imageAttempted) {
      setState(() => error = 'Sprawdź poprzednie zlecenie i rozpocznij nowe.');
      return;
    }
    final cap = int.tryParse(creditCap.text.trim());
    final params = imageParameters();
    final price = imageQuote?['credits_estimated'];
    if (quotedImageParams != jsonEncode(params) || price is! int ||
        cap == null || cap < price) {
      setState(() => error =
        'Pobierz wycenę tych samych parametrów i zatwierdź właściwy limit.');
      return;
    }
    if (!await approve('Generowanie obrazu: $price kredytów', billable: true)) return;
    await run(() async {
      // Record the attempt BEFORE a billable call. Timeouts are ambiguous.
      await _persistImageAttempt(true);
      final data = await post('images/generate', {
        ...params, 'confirmed_reference_rights': true,
        'approved_for_paid_generation': true,
        'max_approved_credits': cap,
      });
      if (mounted) setState(() {
        result = data;
        notice = 'Zadanie zakończone. Następne wymaga osobnej zgody.';
      });
    });
  }

  Future<void> assets() => run(() async {
    final data = await get('assets');
    if (mounted) setState(() { result = data; notice = 'Pobrano zasoby z konta.'; });
  });

  Widget field(String id, String label, TextEditingController controller,
      {int lines = 1}) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 5),
    child: TextField(
      key: Key(id), controller: controller, maxLines: lines,
      decoration: InputDecoration(labelText: label,
        border: const OutlineInputBorder()),
    ),
  );

  Widget fileButton(String mediaKind) => OutlinedButton.icon(
    key: Key('visionstory_select_' + mediaKind),
    onPressed: busy ? null : () => choose(mediaKind),
    icon: const Icon(Icons.upload_file),
    label: Text(mediaKind == 'image' ? 'Wybierz zdjęcie' : 'Wybierz MP3/WAV'),
  );

  Widget approvals() => Column(children: [
    CheckboxListTile(
      key: const Key('media_rights'), value: rights,
      title: const Text('Mam prawa do używanych materiałów'),
      onChanged: (v) => setState(() => rights = v ?? false)),
    CheckboxListTile(
      key: const Key('media_subject_consent'), value: consent,
      title: const Text('Posiadam zgodę właściciela wizerunku lub głosu'),
      onChanged: (v) => setState(() => consent = v ?? false)),
    CheckboxListTile(
      key: const Key('media_paid_consent'), value: paid,
      title: const Text('Akceptuję użycie kredytów na zatwierdzone zadanie'),
      onChanged: (v) => setState(() => paid = v ?? false)),
  ]);

  Widget summary() => Column(children: [
    if (filename != null) Text('Wybrany plik: ' + filename!),
    if (notice != null) Text(notice!, style: const TextStyle(color: Colors.greenAccent)),
    if (result != null) SelectableText(const JsonEncoder.withIndent('  ').convert(result)),
  ]);

  Widget avatarsTab() => ListView(padding: const EdgeInsets.all(12), children: [
    const Text('Awatar z fotografii — wyłącznie za zgodą osoby'),
    fileButton('image'), approvals(),
    FilledButton(key: const Key('visionstory_create_avatar'),
      onPressed: busy ? null : makeAvatar, child: const Text('Utwórz awatar')),
    field('vs_avatar_id', 'ID własnego awatara', avatar),
    DropdownButton<String>(
      key: const Key('vs_frame_ratio'), value: ratio ?? '9:16',
      items: const ['9:16', '16:9', '1:1'].map((r) =>
        DropdownMenuItem(value: r, child: Text(r))).toList(),
      onChanged: (v) => setState(() => ratio = v),
    ),
    OutlinedButton(key: const Key('visionstory_frame_avatar'),
      onPressed: busy ? null : frameAvatar, child: const Text('Ustaw kadr 1:1')),
    summary(),
  ]);

  Widget voiceTab() => ListView(padding: const EdgeInsets.all(12), children: [
    const Text('Klonowanie głosu wymaga zgody jego właściciela'),
    fileButton('audio'),
    field('vs_voice_preview', 'Tekst próbny', voicePreview, lines: 2),
    approvals(),
    FilledButton(key: const Key('visionstory_clone_voice'),
      onPressed: busy ? null : cloneVoice, child: const Text('Klonuj głos')),
    summary(),
  ]);

  List<String> imageOptions(String field) {
    final entries = catalog?['models'];
    if (entries is! List) return [];
    for (final entry in entries) {
      if (entry is! Map || entry['model_id'] != model.text.trim()) continue;
      final params = entry['params'];
      final values = params is Map && params[field] is Map
          ? (params[field] as Map)['values'] : null;
      if (values is List) return values.whereType<String>().toList();
    }
    return [];
  }

  Widget imageTab() => ListView(padding: const EdgeInsets.all(12), children: [
    const Text('Dostępność modeli i ceny są zależne od Twojego konta.'),
    OutlinedButton(key: const Key('visionstory_image_models'),
      onPressed: busy ? null : imageModels,
      child: const Text('Pobierz aktualne modele obrazów')),
    if (catalog?['models'] is List)
      for (final item in catalog!['models'] as List)
        if (item is Map && item['model_id'] is String)
          ListTile(
            title: Text(item['model_id'] as String),
            onTap: () => setState(() {
              model.text = item['model_id'] as String;
              final params = item['params'];
              if (params is Map) {
                final settings = params['resolution'];
                final ratios = params['aspect_ratio'];
                resolution = settings is Map && settings['default'] is String
                    ? settings['default'] as String : null;
                ratio = ratios is Map && ratios['default'] is String
                    ? ratios['default'] as String : null;
                imageQuote = null;
                quotedImageParams = null;
              }
            }),
          ),
    field('vs_image_model', 'ID modelu', model),
    field('vs_image_prompt', 'Opis obrazu', prompt, lines: 3),
    field('vs_image_asset', 'ID zdjęcia referencyjnego (opcjonalne)', asset),
    field('vs_image_credit_cap', 'Limit kredytów', creditCap),
    if (imageOptions('resolution').isNotEmpty)
      DropdownButtonFormField<String>(
        key: const Key('vs_image_resolution'),
        value: imageOptions('resolution').contains(resolution) ? resolution : null,
        decoration: const InputDecoration(labelText: 'Rozdzielczość'),
        items: imageOptions('resolution').map((v) =>
          DropdownMenuItem(value: v, child: Text(v))).toList(),
        onChanged: busy ? null : (v) => setState(() {
          resolution = v; imageQuote = null; quotedImageParams = null;
        })),
    if (imageOptions('aspect_ratio').isNotEmpty)
      DropdownButtonFormField<String>(
        key: const Key('vs_image_ratio'),
        value: imageOptions('aspect_ratio').contains(ratio) ? ratio : null,
        decoration: const InputDecoration(labelText: 'Proporcje obrazu'),
        items: imageOptions('aspect_ratio').map((v) =>
          DropdownMenuItem(value: v, child: Text(v))).toList(),
        onChanged: busy ? null : (v) => setState(() {
          ratio = v; imageQuote = null; quotedImageParams = null;
        })),
    OutlinedButton(
      key: const Key('visionstory_estimate_image'),
      onPressed: busy ? null : estimateImage,
      child: const Text('Sprawdź koszt bez generowania')),
    if (imageQuote != null)
      Text('Wycena: ${imageQuote!['credits_estimated']} kredytów '
           '— ${imageQuote!['resolution']}, ${imageQuote!['aspect_ratio']}'),
    approvals(),
    if (imageAttempted) ...[
      const Text('Poprzednie żądanie mogło zużyć kredyty. '
          'Sprawdź historię VisionStory przed nowym zadaniem.'),
      OutlinedButton(
        key: const Key('visionstory_new_image_attempt'),
        onPressed: busy || !imageStateLoaded ? null : startNewImage,
        child: const Text('Rozpocznij nowe, osobno płatne zadanie')),
    ],
    FilledButton(key: const Key('visionstory_generate_image'),
      onPressed: busy || !imageStateLoaded || imageAttempted ? null : images,
      child: const Text('Zatwierdź i generuj obraz')),
    summary(),
  ]);

  Widget assetsTab() => ListView(padding: const EdgeInsets.all(12), children: [
    OutlinedButton.icon(
      key: const Key('visionstory_media_understanding'),
      onPressed: busy ? null : () => Navigator.of(context).push(
        MaterialPageRoute<void>(builder: (_) => VisionStoryUnderstandingScreen(
          initialServer: host.text, initialGatewayKey: key.text,
        )),
      ),
      icon: const Icon(Icons.document_scanner_outlined),
      label: const Text('Analiza mediów do JSON (1–8 zasobów)'),
    ),
    const Text('Analiza może zużywać kredyty i wymaga osobnego zatwierdzenia.'),
    OutlinedButton(key: const Key('visionstory_assets_refresh'),
      onPressed: busy ? null : assets, child: const Text('Pobierz zasoby z VisionStory')),
    Wrap(spacing: 8, children: [fileButton('image'), fileButton('audio')]),
    approvals(),
    FilledButton(key: const Key('visionstory_upload_asset'),
      onPressed: busy ? null : upload, child: const Text('Prześlij plik')),
    field('vs_asset_id', 'ID zasobu', asset),
    summary(),
  ]);

  @override
  Widget build(BuildContext context) => DefaultTabController(length: 4,
    child: Scaffold(
      appBar: AppBar(title: const Text('VisionStory — Awatary i multimedia'),
        bottom: const TabBar(isScrollable: true, tabs: [
          Tab(text: 'Awatary'), Tab(text: 'Głosy'),
          Tab(text: 'Obrazy'), Tab(text: 'Zasoby'),
        ])),
      body: SafeArea(child: Column(children: [
        ExpansionTile(
          title: const Text('Prywatny backend HTTPS'),
          subtitle: const Text('Klucz producenta pozostaje na serwerze'),
          initiallyExpanded: true,
          children: [
            field('vs_media_host', 'Adres własnego backendu HTTPS', host),
            TextField(key: const Key('vs_media_key'),
              controller: key, obscureText: true,
              autocorrect: false, enableSuggestions: false,
              decoration: const InputDecoration(labelText: 'Klucz gateway')),
          ]),
        if (busy) const LinearProgressIndicator(),
        if (error != null) Text(error!,
          style: TextStyle(color: Theme.of(context).colorScheme.error)),
        Expanded(child: TabBarView(children: [
          avatarsTab(), voiceTab(), imageTab(), assetsTab(),
        ])),
      ])),
    ),
  );
}
