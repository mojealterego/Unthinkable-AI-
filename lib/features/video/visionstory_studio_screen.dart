import 'dart:convert';
import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';

import 'visionstory_gateway.dart';

/// Working integration UI, pending the owner's final film-studio visual design.
/// All purchases must be explicitly confirmed; keys are never persisted.
class VisionStoryStudioScreen extends StatefulWidget {
  const VisionStoryStudioScreen({super.key, this.gateway});
  final VisionStoryGateway? gateway;
  @override State<VisionStoryStudioScreen> createState() => _VisionStoryStudioScreenState();
}

class _VisionStoryStudioScreenState extends State<VisionStoryStudioScreen> {
  late final VisionStoryGateway api;
  final server = TextEditingController();
  final key = TextEditingController();
  final aiModel = TextEditingController();
  final avatarModel = TextEditingController();
  final avatarId = TextEditingController();
  final voiceId = TextEditingController();
  final videoPrompt = TextEditingController();
  final script = TextEditingController();
  final videoId = TextEditingController();
  final audioAssetId = TextEditingController();
  final alignText = TextEditingController();
  final referenceAsset = TextEditingController();
  Map<String, dynamic>? credits, models, avatars, voices, aiModels, lastJob;
  Map<String, dynamic>? transcript;
  int? quote;
  String? quoteId;
  String? error, notice;
  bool busy = false, rights = false, paid = false, srt = true, diarize = false;
  List<int>? audioData;
  String? audioMime;

  @override
  void initState() {
    super.initState();
    api = widget.gateway ?? VisionStoryGateway();
  }

  @override void dispose() {
    for (final item in [server, key, aiModel, avatarModel, avatarId, voiceId,
      videoPrompt, script, videoId, audioAssetId, alignText, referenceAsset]) {
      item.dispose();
    }
    api.close();
    super.dispose();
  }

  Future<void> run(Future<void> Function() operation) async {
    if (busy) return;
    setState(() { busy = true; error = null; notice = null; });
    try {
      await operation();
    } on FormatException catch (e) {
      if (mounted) setState(() => error = e.message);
    } on VisionStoryGatewayError catch (e) {
      if (mounted) setState(() => error = e.message);
    } on Object {
      if (mounted) setState(() => error = 'Nie można wykonać zadania. Sprawdź backend i dane.');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<Map<String, dynamic>> get(String path) => api.call(
    server: server.text, key: key.text, path: path);

  Future<Map<String, dynamic>> post(String path, Map<String, Object?> data) =>
      api.call(server: server.text, key: key.text, path: path, body: data);

  Future<void> loadCatalog() => run(() async {
    final fetched = await Future.wait([
      get('credits'), get('models'), get('avatars'), get('voices'),
      get('models/ai-video'),
    ]);
    if (!mounted) return;
    setState(() {
      credits = fetched[0];
      models = fetched[1];
      avatars = fetched[2];
      voices = fetched[3];
      aiModels = fetched[4];
      notice = 'Pobrano katalogi z Twojego serwera. Niczego nie wygenerowano.';
    });
  });

  Iterable<Map> items(Map<String, dynamic>? catalog, List<String> keys) sync* {
    if (catalog == null) return;
    for (final key in keys) {
      final list = catalog[key];
      if (list is List) {
        for (final item in list) {
          if (item is Map) yield item;
        }
      }
    }
  }

  Map<String, Object?> clipBody({bool submit = false}) {
    if (aiModel.text.trim().isEmpty || videoPrompt.text.trim().isEmpty) {
      throw const FormatException('Wybierz model z katalogu i podaj opis ujęcia.');
    }
    quoteId ??= 'clip_' + DateTime.now().microsecondsSinceEpoch.toString();
    return {
      'model_id': aiModel.text.trim(),
      'prompt': videoPrompt.text.trim(),
      'duration_sec': 8,
      'resolution': '720p',
      'aspect_ratio': '9:16',
      'generate_audio': true,
      'client_request_id': quoteId,
      if (referenceAsset.text.trim().isNotEmpty)
        'refs': [{'asset_id': referenceAsset.text.trim()}],
      'confirmed_media_rights': rights,
      'approved_for_paid_generation': submit && paid,
      'max_approved_credits': submit ? (quote ?? 0) : 0,
    };
  }

  Future<void> estimate() => run(() async {
    quote = null;
    quoteId = null;
    final data = await post('ai-video/estimate', clipBody());
    final value = data['credits_estimated'];
    if (value is! int || value <= 0) throw const FormatException('Błędna wycena.');
    if (!mounted) return;
    setState(() { quote = value; notice = 'Cena ujęcia: ' + value.toString() + ' kredytów.'; });
  });

  Future<bool> confirm(String title, String body) async {
    if (!mounted) return false;
    return await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Text(body),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Anuluj')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Zatwierdź')),
        ],
      ),
    ) ?? false;
  }

  Future<void> generateClip() async {
    if (!rights || !paid) {
      setState(() => error = 'Zaznacz prawa do materiałów i zgodę na wydanie kredytów.');
      return;
    }
    final accepted = await confirm('Płatne generowanie klipu',
      'Wyślij zlecenie za maksymalnie ' + (quote ?? 0).toString() +
      ' kredytów? Wynik otrzyma własny identyfikator zadania.');
    if (!accepted) return;
    await run(() async {
      final data = await post('ai-video', clipBody(submit: true));
      if (!mounted) return;
      setState(() {
        lastJob = data;
        videoId.text = (data['video_id'] ?? '').toString();
        notice = 'Zadanie wysłane. Zachowaj ID i sprawdzaj jego status.';
      });
    });
  }

  Future<void> generateAvatarVideo() async {
    if (!rights || !paid) {
      setState(() => error = 'Potwierdź prawa i zgodę na kredyty.');
      return;
    }
    final accepted = await confirm('Płatny film z awatarem',
      'Utworzyć film na podstawie scenariusza? Usługa może zużyć kredyty.');
    if (!accepted) return;
    await run(() async {
      final data = await post('talking-video', {
        'model_id': avatarModel.text.trim(),
        'avatar_id': avatarId.text.trim(),
        'voice_id': voiceId.text.trim(),
        'text': script.text,
        'client_request_id': 'avatar_' + DateTime.now().microsecondsSinceEpoch.toString(),
        'approved_for_paid_generation': true,
      });
      if (!mounted) return;
      setState(() {
        lastJob = data;
        videoId.text = (data['video_id'] ?? '').toString();
        notice = 'Zadanie awatara zostało przyjęte.';
      });
    });
  }

  Future<void> checkJob({bool aiVideo = true}) => run(() async {
    final id = videoId.text.trim();
    if (!RegExp(r'^[a-zA-Z0-9_.-]{3,160}$').hasMatch(id)) {
      throw const FormatException('Podaj prawidłowy identyfikator zadania.');
    }
    final job = await get((aiVideo ? 'ai-video/' : 'talking-video/') + id);
    if (!mounted) return;
    setState(() { lastJob = job; notice = 'Pobrano aktualny stan zadania.'; });
  });

  Future<void> chooseAudio() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom, allowedExtensions: ['mp3', 'wav'], withData: true);
    if (result == null || result.files.isEmpty) return;
    final picked = result.files.first;
    if (picked.bytes == null || picked.bytes!.isEmpty || picked.bytes!.length > 8000000) {
      if (mounted) setState(() => error = 'Wybierz MP3 lub WAV do 8 MB.');
      return;
    }
    if (mounted) setState(() {
      audioData = picked.bytes;
      audioMime = picked.extension?.toLowerCase() == 'wav' ? 'audio/wav' : 'audio/mpeg';
      notice = 'Załadowano: ' + picked.name;
    });
  }

  Map<String, Object?>? audioRef() {
    if (audioData != null) {
      return {
        'inline_data': {
          'mime_type': audioMime ?? 'audio/mpeg',
          'data': base64Encode(audioData!),
        },
      };
    }
    if (audioAssetId.text.trim().isNotEmpty) {
      return {'asset_id': audioAssetId.text.trim()};
    }
    return null;
  }

  Future<void> transcribe({bool alignment = false}) async {
    if (!rights || !paid) {
      setState(() => error = 'Wymagana zgoda na użycie audio i naliczenie kredytów.');
      return;
    }
    if (audioRef() == null) {
      setState(() => error = 'Załaduj MP3/WAV albo podaj ID swojego pliku audio.');
      return;
    }
    if (!await confirm('Płatne przetwarzanie dźwięku',
        'Wykonać transkrypcję lub dopasowanie słów? Operacja może zużyć kredyty.')) return;
    await run(() async {
      final data = await post(alignment ? 'audio/align' : 'audio/transcribe', {
        'audio': audioRef(),
        if (alignment) 'text': alignText.text,
        if (!alignment) 'diarize': diarize,
        if (!alignment) 'srt': srt,
        'confirmed_audio_rights': true,
        'approved_for_paid_processing': true,
      });
      if (!mounted) return;
      setState(() { transcript = data; notice = 'Przetwarzanie zakończone.'; });
    });
  }

  Future<void> generateSpeech() async {
    if (!rights || !paid) {
      setState(() => error = 'Potwierdź prawa do głosu i zgodę na kredyty.');
      return;
    }
    if (!await confirm('Płatna synteza MP3',
      'Wygenerować MP3 z wybranym głosem? VisionStory nalicza kredyty.')) return;
    await run(() async {
      final bytes = await api.makeMp3(
        server: server.text, key: key.text,
        voiceId: voiceId.text.trim(), text: script.text);
      final folder = await getApplicationDocumentsDirectory();
      final output = File(folder.path + '/visionstory-' +
        DateTime.now().millisecondsSinceEpoch.toString() + '.mp3');
      await output.writeAsBytes(bytes, flush: true);
      if (mounted) setState(() => notice = 'MP3 zapisano w prywatnych plikach aplikacji.');
    });
  }

  @override
  Widget build(BuildContext context) => DefaultTabController(
    length: 3,
    child: Scaffold(
      appBar: AppBar(
        title: const Text('VisionStory — Studio Filmowe'),
        bottom: const TabBar(tabs: [
          Tab(text: 'Katalogi', icon: Icon(Icons.collections_bookmark_outlined)),
          Tab(text: 'Wideo', icon: Icon(Icons.movie_outlined)),
          Tab(text: 'Audio', icon: Icon(Icons.music_note)),
        ]),
      ),
      body: SafeArea(child: Column(children: [
        ExpansionTile(
          title: const Text('Prywatny backend HTTPS'),
          subtitle: const Text('Klucz VisionStory pozostaje na serwerze; tutaj tylko gateway.'),
          childrenPadding: const EdgeInsets.all(12),
          children: [
            TextField(key: const Key('visionstory_url'), controller: server,
              keyboardType: TextInputType.url,
              decoration: const InputDecoration(labelText: 'Adres backendu HTTPS')),
            TextField(key: const Key('visionstory_gateway_key'), controller: key,
              obscureText: true, enableSuggestions: false, autocorrect: false,
              decoration: const InputDecoration(labelText: 'Klucz gateway')),
          ],
        ),
        if (busy) const LinearProgressIndicator(),
        if (error != null) Padding(padding: const EdgeInsets.all(8),
          child: Text(error!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
        if (notice != null) Padding(padding: const EdgeInsets.all(8),
          child: Text(notice!, style: const TextStyle(color: Colors.greenAccent))),
        Expanded(child: TabBarView(children: [
          ListView(padding: const EdgeInsets.all(16), children: [
            const Text('Aktualne katalogi i saldo z konta VisionStory.'),
            FilledButton.icon(key: const Key('visionstory_discover'),
              onPressed: busy ? null : loadCatalog,
              icon: const Icon(Icons.sync), label: const Text('Pobierz katalogi i kredyty')),
            if (credits != null) Text('Kredyty: ' + (credits!['remaining'] ?? '—').toString()),
            for (final group in [
              ('Modele awatara', models, ['models']),
              ('Modele klipów AI', aiModels, ['models']),
              ('Awatary', avatars, ['my_avatars', 'public_avatars', 'avatars']),
              ('Głosy', voices, ['public_voices', 'my_voices', 'voices']),
            ]) ...[
              const SizedBox(height: 16),
              Text(group.$1, style: Theme.of(context).textTheme.titleMedium),
              for (final item in items(group.$2, group.$3))
                ListTile(
                  title: Text((item['model_id'] ?? item['avatar_id'] ??
                    item['voice_id'] ?? 'Element').toString()),
                  subtitle: Text((item['description'] ?? item['locale'] ?? '').toString(),
                    maxLines: 2),
                  trailing: const Icon(Icons.arrow_circle_right_outlined),
                  onTap: () => setState(() {
                    if (group.$1 == 'Modele awatara') {
                      avatarModel.text = (item['model_id'] ?? '').toString();
                    } else if (group.$1 == 'Modele klipów AI') {
                      aiModel.text = (item['model_id'] ?? '').toString();
                      quote = null; quoteId = null;
                    } else if (group.$1 == 'Awatary') {
                      avatarId.text = (item['avatar_id'] ?? '').toString();
                    } else {
                      voiceId.text = (item['voice_id'] ?? '').toString();
                    }
                  }),
                ),
            ],
          ]),
          ListView(padding: const EdgeInsets.all(16), children: [
            Text('Generowanie klipów z referencjami',
              style: Theme.of(context).textTheme.titleLarge),
            _field('visionstory_clip_model', aiModel, 'Model wideo (wybierz z katalogu)'),
            _field('visionstory_clip_prompt', videoPrompt, 'Opis klipu / sceny', maxLines: 3),
            _field('visionstory_clip_ref', referenceAsset, 'ID zdjęcia referencyjnego (opcjonalnie)'),
            FilledButton(key: const Key('visionstory_quote'),
              onPressed: busy ? null : estimate, child: const Text('Oblicz koszt u dostawcy')),
            if (quote != null) Text('Wycena: ' + quote.toString() + ' kredytów'),
            _permissions(),
            FilledButton(key: const Key('visionstory_submit_clip'),
              onPressed: busy || quote == null ? null : generateClip,
              child: const Text('Zatwierdź i generuj klip')),
            const Divider(height: 36),
            Text('Mówiący awatar', style: Theme.of(context).textTheme.titleLarge),
            _field('visionstory_avatar_model', avatarModel, 'Model awatara'),
            _field('visionstory_avatar_id', avatarId, 'ID awatara'),
            _field('visionstory_voice_id', voiceId, 'ID głosu'),
            _field('visionstory_script', script, 'Tekst do wypowiedzenia', maxLines: 3),
            OutlinedButton(key: const Key('visionstory_submit_avatar'),
              onPressed: busy ? null : generateAvatarVideo,
              child: const Text('Zatwierdź i generuj mówiący film')),
            const Divider(height: 36),
            Text('Zadania', style: Theme.of(context).textTheme.titleLarge),
            _field('visionstory_video_id', videoId, 'ID otrzymanego zadania'),
            Row(children: [
              Expanded(child: TextButton(
                onPressed: busy ? null : () => checkJob(aiVideo: true),
                child: const Text('Status klipu AI'),
              )),
              Expanded(child: TextButton(
                onPressed: busy ? null : () => checkJob(aiVideo: false),
                child: const Text('Status awatara'),
              )),
            ]),
            if (lastJob != null) SelectableText(
              const JsonEncoder.withIndent('  ').convert(lastJob)),
            const Text('MP4 jest archiwizowane przez backend po konfiguracji wolumenu/CDN.'),
          ]),
          ListView(padding: const EdgeInsets.all(16), children: [
            Text('Dźwięk, SRT i synchronizacja',
              style: Theme.of(context).textTheme.titleLarge),
            _permissions(),
            OutlinedButton.icon(key: const Key('visionstory_pick_audio'),
              onPressed: busy ? null : chooseAudio,
              icon: const Icon(Icons.upload_file), label: const Text('Wybierz MP3/WAV (do 8 MB)')),
            _field('visionstory_audio_asset', audioAssetId,
              'Lub ID własnego pliku audio u dostawcy'),
            CheckboxListTile(value: srt, title: const Text('Generuj napisy SRT'),
              onChanged: (v) => setState(() => srt = v ?? false)),
            CheckboxListTile(value: diarize, title: const Text('Rozpoznaj mówców'),
              onChanged: (v) => setState(() => diarize = v ?? false)),
            FilledButton(key: const Key('visionstory_transcribe'),
              onPressed: busy ? null : () => transcribe(),
              child: const Text('Zatwierdź transkrypcję')),
            _field('visionstory_alignment_text', alignText,
              'Znany tekst do dopasowania', maxLines: 3),
            TextButton(key: const Key('visionstory_align'),
              onPressed: busy ? null : () => transcribe(alignment: true),
              child: const Text('Dopasuj tekst do nagrania')),
            if (transcript != null) ...[
              SelectableText(const JsonEncoder.withIndent('  ').convert(transcript)),
              if (transcript!['srt'] is String)
                OutlinedButton(
                  onPressed: () => Clipboard.setData(
                    ClipboardData(text: transcript!['srt'] as String)),
                  child: const Text('Kopiuj SRT'),
                ),
            ],
            const Divider(height: 28),
            const Text('Synteza głosu do MP3 (zapis w pamięci aplikacji)'),
            _field('visionstory_tts_voice', voiceId, 'ID wybranego głosu'),
            _field('visionstory_tts_text', script, 'Tekst do MP3', maxLines: 3),
            FilledButton(key: const Key('visionstory_tts'),
              onPressed: busy ? null : generateSpeech,
              child: const Text('Zatwierdź i wygeneruj MP3')),
          ]),
        ])),
      ])),
    ),
  );

  Widget _field(String id, TextEditingController controller, String label,
      {int maxLines = 1}) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 6),
    child: TextField(
      key: Key(id), controller: controller, maxLines: maxLines,
      onChanged: (_) {
        if (id == 'visionstory_clip_model' || id == 'visionstory_clip_prompt' ||
            id == 'visionstory_clip_ref') setState(() { quote = null; quoteId = null; });
      },
      decoration: InputDecoration(
        labelText: label, border: const OutlineInputBorder()),
    ),
  );

  Widget _permissions() => Column(children: [
    CheckboxListTile(
      key: const Key('visionstory_rights'),
      value: rights, title: const Text('Potwierdzam prawa i zgody do materiałów'),
      onChanged: (v) => setState(() => rights = v ?? false),
    ),
    CheckboxListTile(
      key: const Key('visionstory_paid'),
      value: paid, title: const Text('Zezwalam na operację zużywającą kredyty'),
      onChanged: (v) => setState(() => paid = v ?? false),
    ),
  ]);
}
