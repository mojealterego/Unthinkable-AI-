import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'visionstory_api.dart';

/// Functional first-party Cinema provider controls. Visual assets are supplied
/// separately by the owner; no external artwork or pretend render buttons.
class VisionStoryScreen extends StatefulWidget {
  const VisionStoryScreen({super.key, this.api});
  final VisionStoryApi? api;
  @override
  State<VisionStoryScreen> createState() => _VisionStoryScreenState();
}

class _VisionStoryScreenState extends State<VisionStoryScreen> {
  static const _jobKey = 'unthinkable.cinema.visionstory.job.v1';
  late final VisionStoryApi api;
  final _host = TextEditingController();
  final _key = TextEditingController();
  final _script = TextEditingController(text: 'Witaj w Unthinkable AI.');
  final _jobLookup = TextEditingController();

  List<String> _models = [], _avatars = [], _voices = [];
  String? _model, _avatar, _voice, _videoId, _requestId;
  List<int>? _audio;
  String? _audioMime;
  String? _error, _message, _transcript;
  bool _pending = false, _loading = false, _approved = false, _rights = false;
  bool _fromAudio = false, _withSrt = true, _diarize = false;
  Map<String, dynamic>? _status;
  int? _credits;

  @override
  void initState() {
    super.initState();
    api = widget.api ?? VisionStoryApi();
    _restore();
  }

  Future<void> _restore() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;
    setState(() {
      _requestId = prefs.getString(_jobKey + '.request');
      _videoId = prefs.getString(_jobKey + '.video');
      _pending = prefs.getBool(_jobKey + '.pending') ?? false;
      _jobLookup.text = _videoId ?? '';
    });
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    if (_requestId != null) await prefs.setString(_jobKey + '.request', _requestId!);
    if (_videoId != null) await prefs.setString(_jobKey + '.video', _videoId!);
    await prefs.setBool(_jobKey + '.pending', _pending);
  }

  @override
  void dispose() {
    _host.dispose();
    _key.clear();
    _key.dispose();
    _script.dispose();
    _jobLookup.dispose();
    api.dispose();
    super.dispose();
  }

  List<String> _ids(Map<String, dynamic> json, List<String> groups, String key) {
    final output = <String>{};
    for (final group in groups) {
      for (final row in json[group] is List ? json[group] as List : []) {
        if (row is Map && row[key] is String && (row[key] as String).isNotEmpty) {
          output.add(row[key] as String);
        }
      }
    }
    return output.toList();
  }

  Future<void> _load() => _task(() async {
    final results = await Future.wait([
      api.credits(_host.text, _key.text),
      api.models(_host.text, _key.text),
      api.avatars(_host.text, _key.text),
      api.voices(_host.text, _key.text),
    ]);
    if (!mounted) return;
    final models = _ids(results[1], ['models'], 'model_id');
    final avatars = _ids(results[2],
        ['avatars', 'my_avatars', 'public_avatars'], 'avatar_id');
    final voices = _ids(results[3],
        ['voices', 'my_voices', 'public_voices'], 'voice_id');
    setState(() {
      _credits = results[0]['remaining'] is int ? results[0]['remaining'] as int : null;
      _models = models;
      _avatars = avatars;
      _voices = voices;
      _model = models.contains(_model) ? _model : (models.isEmpty ? null : models.first);
      _avatar = avatars.contains(_avatar) ? _avatar : (avatars.isEmpty ? null : avatars.first);
      _voice = voices.contains(_voice) ? _voice : (voices.isEmpty ? null : voices.first);
      _message = 'Katalogi pobrane z Twojego konta dostawcy.';
    });
  });

  Future<void> _task(Future<void> Function() work) async {
    if (_loading) return;
    setState(() { _loading = true; _error = null; _message = null; });
    try {
      await work();
    } on Object catch (error) {
      if (mounted) {
        setState(() => _error =
            error is VisionStoryClientError ? error.message :
            error is FormatException ? error.message : 'Operacja nie została wykonana.');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _chooseAudio() async {
    try {
      final selected = await FilePicker.platform.pickFiles(
          type: FileType.custom, allowedExtensions: ['mp3', 'wav', 'm4a'],
          withData: true);
      if (selected == null || selected.files.isEmpty) return;
      final asset = selected.files.single;
      if (asset.size > 8 * 1000 * 1000) {
        throw const FormatException('Maksymalny rozmiar pliku: 8 MB.');
      }
      final bytes = asset.bytes ?? (asset.path == null
          ? null : await File(asset.path!).readAsBytes());
      if (bytes == null || bytes.isEmpty) throw const FormatException('Nie można odczytać audio.');
      final ext = asset.extension?.toLowerCase();
      if (mounted) setState(() {
        _audio = bytes;
        _audioMime = ext == 'wav' ? 'audio/wav' :
            ext == 'm4a' ? 'audio/m4a' : 'audio/mpeg';
        _message = 'Wybrano: ' + asset.name;
      });
    } on Object {
      if (mounted) setState(() => _error = 'Nie udało się zaimportować MP3/WAV/M4A.');
    }
  }

  Future<void> _submit() => _task(() async {
    if (_model == null || _avatar == null || (!_fromAudio && _voice == null)) {
      throw const FormatException('Najpierw pobierz i wybierz model, awatar oraz głos.');
    }
    if (_pending) {
      throw const FormatException('Poprzednie zadanie ma nieustalony status. Najpierw je sprawdź.');
    }
    if (!_approved) throw const FormatException('Wymagana akceptacja kosztu.');
    if (_fromAudio && (!_rights || _audio == null || _audioMime == null)) {
      throw const FormatException('Dodaj audio i potwierdź prawo do nagrania.');
    }
    // Record request_id BEFORE the paid call to survive an ambiguous timeout.
    final requestId = 'cinema_' + DateTime.now().microsecondsSinceEpoch.toString();
    setState(() { _requestId = requestId; _pending = true; });
    await _persist();
    final result = _fromAudio
      ? await api.submitAudio(host: _host.text, key: _key.text,
          avatarId: _avatar!, modelId: _model!, data: _audio!,
          mime: _audioMime!, requestId: requestId,
          approved: _approved, rights: _rights)
      : await api.submitText(host: _host.text, key: _key.text,
          avatarId: _avatar!, modelId: _model!, voiceId: _voice!,
          text: _script.text, requestId: requestId, approved: _approved);
    if (result['video_id'] is! String ||
        !VisionStoryApiIsValidId.check(result['video_id'] as String)) {
      throw const FormatException('Brak prawidłowego ID zlecenia. Nie ponawiaj automatycznie.');
    }
    if (!mounted) return;
    setState(() {
      _videoId = result['video_id'] as String;
      _jobLookup.text = _videoId!;
      _pending = false;
      _message = 'Zlecenie przyjęte. Sprawdź status i koszt u dostawcy.';
    });
    await _persist();
  });

  Future<void> _poll() => _task(() async {
    final video = _jobLookup.text.trim();
    final result = await api.status(_host.text, _key.text, video);
    if (!mounted) return;
    setState(() { _status = result; _videoId = video; _message = 'Pobrano aktualny status.'; });
    await _persist();
  });

  Future<void> _archive() => _task(() async {
    final video = _jobLookup.text.trim();
    final result = await api.archive(_host.text, _key.text, video);
    if (mounted) setState(() => _message =
        result['archived'] == true ? 'Film zapisany na prywatnym serwerze.' : 'Archiwizacja niepotwierdzona.');
  });

  Future<void> _download() => _task(() async {
    final file = await api.downloadMp4(_host.text, _key.text, _jobLookup.text.trim());
    if (mounted) setState(() => _message = 'MP4 zapisany lokalnie: ' + file.path);
  });

  Future<void> _transcribe() => _task(() async {
    if (_audio == null || _audioMime == null || !_rights || !_approved) {
      throw const FormatException('Wybierz MP3/WAV i potwierdź prawa oraz koszt.');
    }
    final result = await api.transcribe(
      host: _host.text, key: _key.text,
      data: _audio!, mime: _audioMime!,
      approved: _approved, rights: _rights,
      srt: _withSrt, diarize: _diarize,
    );
    if (mounted) setState(() {
      _transcript = _withSrt && result['srt'] is String
          ? result['srt'] as String : (result['text'] ?? '').toString();
      _message = 'Wynik transkrypcji został odebrany.';
    });
  });

  Future<void> _tts() => _task(() async {
    if (_voice == null || !_rights || !_approved) {
      throw const FormatException('Wybierz głos i potwierdź prawa oraz koszt.');
    }
    final saved = await api.synthesizeTts(
      host: _host.text, key: _key.text, text: _script.text,
      voiceId: _voice!, approved: _approved, rights: _rights,
    );
    if (mounted) setState(() => _message = 'MP3 zapisany: ' + saved.path);
  });

  Future<void> _newRequest() async {
    final agree = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
      title: const Text('Rozpocząć nowe zlecenie?'),
      content: const Text('Poprzednie zlecenie mogło pobrać kredyty. '
          'Sprawdź je najpierw w VisionStory. Nowa próba może kosztować kolejne kredyty.'),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Anuluj')),
        FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Nowe zlecenie')),
      ],
    ));
    if (agree != true || !mounted) return;
    setState(() {
      _videoId = null; _requestId = null; _pending = false; _status = null;
      _jobLookup.clear();
    });
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_jobKey + '.request');
    await prefs.remove(_jobKey + '.video');
    await prefs.setBool(_jobKey + '.pending', false);
  }

  Widget _selector(String title, List<String> values, String? selected,
      ValueChanged<String?> changed) {
    return DropdownButtonFormField<String>(
      value: values.contains(selected) ? selected : null,
      isExpanded: true, decoration: InputDecoration(labelText: title),
      items: values.map((v) => DropdownMenuItem<String>(
        value: v, child: Text(v, overflow: TextOverflow.ellipsis),
      )).toList(),
      onChanged: values.isEmpty ? null : changed,
    );
  }

  @override Widget build(BuildContext context) {
    return DefaultTabController(length: 3, child: Scaffold(
      appBar: AppBar(
        title: const Text('VisionStory • Studio Filmowe'),
        bottom: const TabBar(tabs: [
          Tab(text: 'Awatary', icon: Icon(Icons.face_retouching_natural)),
          Tab(text: 'Zadania MP4', icon: Icon(Icons.movie_filter_outlined)),
          Tab(text: 'Audio / Napisy', icon: Icon(Icons.subtitles_outlined)),
        ]),
      ),
      body: SafeArea(child: Column(children: [
        ExpansionTile(
          initiallyExpanded: true,
          title: const Text('Połączenie z serwerem'),
          subtitle: const Text('Klucz VisionStory pozostaje na backendzie'),
          childrenPadding: const EdgeInsets.all(12),
          children: [
            TextField(key: const Key('vs_host'), controller: _host,
              decoration: const InputDecoration(labelText: 'Adres własnego backendu HTTPS')),
            TextField(key: const Key('vs_key'), controller: _key, obscureText: true,
              enableSuggestions: false, autocorrect: false,
              decoration: const InputDecoration(labelText: 'Klucz dostępu do backendu')),
            const SizedBox(height: 8),
            FilledButton.icon(
              key: const Key('vs_discover'), onPressed: _loading ? null : _load,
              icon: const Icon(Icons.sync), label: const Text('Pobierz modele, awatary i głosy'),
            ),
            if (_credits != null) Text('Kredyty VisionStory: ' + _credits.toString()),
          ],
        ),
        if (_loading) const LinearProgressIndicator(),
        if (_error != null) Padding(padding: const EdgeInsets.all(8),
            child: Text(_error!, style: const TextStyle(color: Colors.orangeAccent))),
        if (_message != null) Padding(padding: const EdgeInsets.all(8),
            child: SelectableText(_message!)),
        Expanded(child: TabBarView(children: [
          ListView(padding: const EdgeInsets.all(16), children: [
            Text('Generator mówiącego awatara', style: Theme.of(context).textTheme.titleLarge),
            _selector('Model', _models, _model, (v) => setState(() => _model = v)),
            _selector('Awatar', _avatars, _avatar, (v) => setState(() => _avatar = v)),
            SwitchListTile(
              title: const Text('Użyj dołączonego MP3/WAV zamiast tekstu'),
              value: _fromAudio, onChanged: (v) => setState(() => _fromAudio = v),
            ),
            if (!_fromAudio) ...[
              _selector('Głos', _voices, _voice, (v) => setState(() => _voice = v)),
              TextField(key: const Key('vs_script'), controller: _script,
                maxLines: 5, minLines: 2,
                decoration: const InputDecoration(labelText: 'Scenariusz awatara')),
            ] else OutlinedButton.icon(onPressed: _chooseAudio,
              icon: const Icon(Icons.audio_file), label: const Text('Dodaj MP3 / WAV / M4A')),
            CheckboxListTile(value: _rights,
              onChanged: (v) => setState(() => _rights = v ?? false),
              title: const Text('Posiadam prawa do używanych mediów i głosu')),
            CheckboxListTile(value: _approved,
              onChanged: (v) => setState(() => _approved = v ?? false),
              title: const Text('Zatwierdzam potencjalne zużycie kredytów')),
            FilledButton.icon(
              key: const Key('vs_submit'), onPressed: _loading || _pending ? null : _submit,
              icon: const Icon(Icons.play_arrow),
              label: const Text('Wyślij zlecenie renderowania')),
            if (_pending)
              const Text('Poprzednie żądanie może nadal być rozliczone. Nie ponawiaj go.'),
            const Text('Brak automatycznego ponawiania płatnych zadań.'),
          ]),
          ListView(padding: const EdgeInsets.all(16), children: [
            Text('Kolejka i archiwum MP4', style: Theme.of(context).textTheme.titleLarge),
            TextField(key: const Key('vs_video_id'), controller: _jobLookup,
              decoration: const InputDecoration(labelText: 'Video ID zlecenia')),
            const SizedBox(height: 10),
            OutlinedButton(onPressed: _loading ? null : _poll,
              child: const Text('Sprawdź aktualny status')),
            if (_status != null) SelectableText(_status.toString()),
            OutlinedButton(onPressed: _loading ? null : _archive,
              child: const Text('Archiwizuj MP4 na serwerze')),
            FilledButton(onPressed: _loading ? null : _download,
              child: const Text('Pobierz MP4 na telefon')),
            TextButton(onPressed: _newRequest,
              child: const Text('Nowe zlecenie (osobny koszt)')),
            const Text('Zapis na telefonie: prywatny katalog Unthinkable AI. '
                'Dostawca przechowuje gotowe filmy przez ograniczony czas.'),
          ]),
          ListView(padding: const EdgeInsets.all(16), children: [
            Text('Studio mowy i napisów', style: Theme.of(context).textTheme.titleLarge),
            _selector('Głos do TTS', _voices, _voice, (v) => setState(() => _voice = v)),
            TextField(controller: _script, maxLines: 3,
              decoration: const InputDecoration(labelText: 'Tekst mowy')),
            FilledButton(onPressed: _loading ? null : _tts,
              child: const Text('Wygeneruj i zapisz MP3')),
            const Divider(height: 26),
            OutlinedButton.icon(onPressed: _chooseAudio,
              icon: const Icon(Icons.audio_file_outlined),
              label: const Text('Dodaj nagranie do transkrypcji')),
            CheckboxListTile(value: _withSrt,
              title: const Text('Utwórz napisy SRT'),
              onChanged: (v) => setState(() => _withSrt = v ?? false)),
            CheckboxListTile(value: _diarize,
              title: const Text('Rozpoznaj rozmówców (opcjonalnie)'),
              onChanged: (v) => setState(() => _diarize = v ?? false)),
            FilledButton(onPressed: _loading ? null : _transcribe,
              child: const Text('Transkrybuj audio')),
            if (_transcript != null) SelectableText(_transcript!),
            const Text('Do generowania TTS i transkrypcji używana jest '
                'wspólna zgoda na prawa do treści oraz koszt z zakładki Awatary.'),
          ]),
        ])),
      ])),
    ));
  }
}

class VisionStoryApiIsValidId {
  static bool check(String id) =>
      RegExp(r'^[A-Za-z0-9_-]{3,160}$').hasMatch(id);
}
