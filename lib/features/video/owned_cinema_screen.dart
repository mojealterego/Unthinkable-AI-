import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';

/// First-party editor. No provider accounts, credits or third-party uploads.
class OwnedCinemaScreen extends StatefulWidget {
  const OwnedCinemaScreen({super.key});
  @override
  State<OwnedCinemaScreen> createState() => _OwnedCinemaScreenState();
}

class _OwnedCinemaScreenState extends State<OwnedCinemaScreen> {
  final _server = TextEditingController();
  final _key = TextEditingController();
  final _title = TextEditingController(text: 'Mój film');
  final _client = http.Client();
  final _clips = <Map<String, String>>[];
  String? _musicId, _jobId, _error, _notice;
  Map<String, dynamic>? _job;
  bool _busy = false, _rights = false, _approve = false;
  int _nextId = 0;

  @override
  void dispose() {
    _server.dispose(); _key.clear(); _key.dispose();
    _title.dispose(); _client.close(); super.dispose();
  }

  Uri _url(String path) {
    final u = Uri.tryParse(_server.text.trim());
    if (u == null || u.scheme != 'https' || u.host.isEmpty ||
        u.userInfo.isNotEmpty || u.hasQuery || u.hasFragment ||
        (u.path.isNotEmpty && u.path != '/')) {
      throw const FormatException('Podaj adres własnego serwera HTTPS.');
    }
    return u.replace(path: '/api/cinema/owned/' + path);
  }

  String _token() {
    final value = _key.text.trim();
    if (value.isEmpty || value.contains('\r') || value.contains('\n')) {
      throw const FormatException('Wprowadź klucz własnego serwera.');
    }
    return value;
  }

  Future<Map<String, dynamic>> _response(http.Response response) async {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw FormatException('Serwer odrzucił operację: HTTP ' +
          response.statusCode.toString());
    }
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException('Niepoprawna odpowiedź serwera.');
    }
    return decoded;
  }

  Future<void> _run(Future<void> Function() action) async {
    if (_busy) return;
    setState(() { _busy = true; _error = null; _notice = null; });
    try {
      await action();
    } on FormatException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } on Object {
      if (mounted) setState(() =>
          _error = 'Nie udało się wykonać operacji. Sprawdź serwer i multimedia.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _import() => _run(() async {
    final selection = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['mp4', 'mov', 'mp3', 'wav', 'm4a'],
    );
    if (selection == null || selection.files.isEmpty) return;
    final picked = selection.files.single;
    if (picked.path == null) {
      throw const FormatException('Brak dostępu do wybranego pliku.');
    }
    final extension = (picked.extension ?? '').toLowerCase();
    const mime = {'mp4': 'video/mp4', 'mov': 'video/quicktime',
      'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'm4a': 'audio/mp4'};
    if (!mime.containsKey(extension) || picked.size > 512 * 1024 * 1024) {
      throw const FormatException('Niedozwolony format lub plik ponad 512 MiB.');
    }
    final file = File(picked.path!);
    final assetId = 'owned_' + DateTime.now().microsecondsSinceEpoch.toString() +
        '_' + (_nextId++).toString();
    final request = http.StreamedRequest(
      'PUT', _url('assets/' + assetId).replace(
        queryParameters: {'extension': extension},
      ),
    );
    request.headers['Authorization'] = 'Bearer ' + _token();
    request.headers['Content-Type'] = mime[extension]!;
    request.contentLength = await file.length();
    request.followRedirects = false;
    final responseFuture = _client.send(request);
    await request.sink.addStream(file.openRead());
    await request.sink.close();
    final result = await _response(
      await http.Response.fromStream(
        await responseFuture.timeout(const Duration(minutes: 15)),
      ),
    );
    if (!mounted) return;
    setState(() {
      final stored = result['asset_id'].toString();
      if (const {'mp3', 'wav', 'm4a'}.contains(extension)) {
        _musicId = stored;
      } else {
        _clips.add({'id': stored, 'name': picked.name, 'seconds': '5'});
      }
      _notice = 'Dodano do własnej biblioteki: ' + picked.name;
      _jobId = null; _job = null;
    });
  });

  Future<void> _render() => _run(() async {
    if (_clips.isEmpty) {
      throw const FormatException('Dodaj przynajmniej jedno własne nagranie.');
    }
    final clips = <Map<String, Object>>[];
    for (final clip in _clips) {
      final seconds = double.tryParse(
        (clip['seconds'] ?? '').replaceAll(',', '.'),
      );
      if (seconds == null || seconds <= 0 || seconds > 3600) {
        throw const FormatException('Podaj prawidłową długość klipu.');
      }
      clips.add({
        'asset_id': clip['id']!,
        'trim_start_ms': 0,
        'duration_ms': (seconds * 1000).round(),
      });
    }
    final requestedId = _jobId ??
      'render_' + DateTime.now().microsecondsSinceEpoch.toString();
    final payload = {
      'project': {
        'title': _title.text.trim(), 'clips': clips,
        'soundtrack_asset_id': _musicId,
        'width': 1280, 'height': 720, 'fps': 25,
      },
      'request_id': requestedId,
      'confirmed_media_rights': _rights,
      'approved_for_local_render': _approve,
    };
    final response = await _client.post(
      _url('renders'),
      headers: {'Authorization': 'Bearer ' + _token(),
        'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    ).timeout(const Duration(seconds: 30));
    final result = await _response(response);
    if (mounted) setState(() {
      _jobId = result['render_id'] as String?;
      _job = result;
      _notice = 'Render zlecono naszemu serwerowi, bez obcych platform.';
    });
  });

  Future<void> _check() => _run(() async {
    if (_jobId == null) return;
    final response = await _client.get(
      _url('renders/' + _jobId!),
      headers: {'Authorization': 'Bearer ' + _token()},
    ).timeout(const Duration(seconds: 30));
    final result = await _response(response);
    if (mounted) setState(() => _job = result);
  });

  Future<void> _download() => _run(() async {
    if (_jobId == null) return;
    final request = http.Request('GET',
      _url('renders/' + _jobId! + '/file'))
      ..headers['Authorization'] = 'Bearer ' + _token()
      ..followRedirects = false;
    final response = await _client.send(request)
        .timeout(const Duration(seconds: 30));
    if (response.statusCode != 200) {
      throw const FormatException('Film nie jest jeszcze dostępny do pobrania.');
    }
    final folder = Directory(
      (await getApplicationDocumentsDirectory()).path + '/unthinkable_cinema',
    );
    await folder.create(recursive: true);
    final output = File(folder.path + '/' + _jobId! + '.mp4');
    final partial = File(folder.path + '/.' + _jobId! + '.partial');
    try {
      final sink = partial.openWrite();
      var count = 0;
      try {
        await for (final bytes in response.stream.timeout(const Duration(minutes: 20))) {
          count += bytes.length;
          if (count > 1024 * 1024 * 1024) {
            throw const FormatException('Eksport przekroczył limit 1 GiB.');
          }
          sink.add(bytes);
        }
      } finally {
        await sink.close();
      }
      if (count < 12) throw const FormatException('Pusty eksport MP4.');
      final header = await partial.openRead(0, 12)
          .fold<List<int>>(<int>[], (a, b) => a..addAll(b));
      if (header.length < 12 ||
          String.fromCharCodes(header.sublist(4, 8)) != 'ftyp') {
        throw const FormatException('Nieprawidłowy kontener MP4.');
      }
      if (await output.exists()) await output.delete();
      await partial.rename(output.path);
      if (mounted) setState(() =>
        _notice = 'Własny MP4 zapisano w pamięci aplikacji.');
    } finally {
      if (await partial.exists()) await partial.delete();
    }
  });

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Unthinkable Cinema — własne Studio')),
    body: SafeArea(child: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('Twoje materiały, nasz serwer. Montaż i ścieżka MP3 '
            'bez żadnego konta ani kredytów VisionStory.'),
        TextField(key: const Key('cinema_own_server'), controller: _server,
          decoration: const InputDecoration(labelText: 'Własny serwer HTTPS')),
        TextField(key: const Key('cinema_own_key'), controller: _key,
          obscureText: true, enableSuggestions: false, autocorrect: false,
          decoration: const InputDecoration(labelText: 'Klucz naszego serwera')),
        TextField(controller: _title,
          decoration: const InputDecoration(labelText: 'Tytuł projektu')),
        const SizedBox(height: 12),
        FilledButton.icon(
          key: const Key('cinema_own_import'),
          onPressed: _busy ? null : _import,
          icon: const Icon(Icons.video_library_outlined),
          label: const Text('Importuj MP4 / MOV / MP3 / WAV')),
        if (_musicId != null) const ListTile(
          leading: Icon(Icons.music_note), title: Text('Dodano ścieżkę muzyczną')),
        for (final clip in _clips) Card(child: Column(children: [
          ListTile(
            title: Text(clip['name'] ?? ''),
            subtitle: const Text('Własny klip do montażu'),
            trailing: IconButton(
              icon: const Icon(Icons.delete_outline),
              onPressed: () => setState(() {
                _clips.remove(clip); _job = null; _jobId = null;
              }),
            ),
          ),
          Padding(padding: const EdgeInsets.symmetric(horizontal: 12),
            child: TextFormField(
              initialValue: clip['seconds'],
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Czas ujęcia [s]'),
              onChanged: (text) {
                clip['seconds'] = text;
                _job = null; _jobId = null;
              },
            )),
        ])),
        CheckboxListTile(
          value: _rights,
          onChanged: (x) => setState(() => _rights = x ?? false),
          title: const Text('Potwierdzam prawa do wykorzystywanych materiałów')),
        CheckboxListTile(
          value: _approve,
          onChanged: (x) => setState(() => _approve = x ?? false),
          title: const Text('Zatwierdzam render na własnej infrastrukturze')),
        FilledButton.icon(
          key: const Key('cinema_own_render'),
          onPressed: _busy || _clips.isEmpty || !_rights || !_approve ? null : _render,
          icon: const Icon(Icons.movie_creation_outlined),
          label: const Text('Zmontuj i wyrenderuj MP4')),
        if (_jobId != null) ...[
          Text('Zadanie: ' + _jobId! + ' • ' +
              (_job?['status'] ?? 'queued').toString()),
          OutlinedButton(
            key: const Key('cinema_own_status'),
            onPressed: _busy ? null : _check,
            child: const Text('Odśwież status')),
          if (_job?['status'] == 'completed')
            OutlinedButton(
              key: const Key('cinema_own_download'),
              onPressed: _busy ? null : _download,
              child: const Text('Pobierz gotowy MP4')),
        ],
        if (_busy) const LinearProgressIndicator(),
        if (_error != null) Text(_error!,
          style: const TextStyle(color: Colors.orangeAccent)),
        if (_notice != null) Text(_notice!),
        const SizedBox(height: 16),
        const Text('Generatory własnych modeli wideo, awatarów, lip-sync '
            'i pełne NLE są kolejnymi etapami. To działający montaż własnych plików.'),
      ],
    )),
  );
}
