import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';

/// Own Unthinkable AI media worker. Never calls a VisionStory account.
class OwnFilmClient {
  OwnFilmClient({http.Client? httpClient})
      : client = httpClient ?? http.Client(), ownsClient = httpClient == null;
  final http.Client client;
  final bool ownsClient;
  void close() { if (ownsClient) client.close(); }

  Uri url(String server, String operation) {
    final uri = Uri.tryParse(server.trim());
    if (uri == null || uri.host.isEmpty || uri.userInfo.isNotEmpty ||
        uri.hasQuery || uri.hasFragment ||
        (uri.path.isNotEmpty && uri.path != '/') ||
        !(uri.scheme == 'https' ||
          (uri.scheme == 'http' && (uri.host == '127.0.0.1' ||
            uri.host == 'localhost' || uri.host == '::1'))) ||
        operation.contains('..') || operation.startsWith('/')) {
      throw const FormatException('Wprowadź adres własnego serwera HTTPS.');
    }
    return uri.replace(path: '/api/film-studio/' + operation);
  }

  Map<String, String> headers(String secret, {String? mime}) {
    final key = secret.trim();
    if (key.isEmpty || key.contains('\r') || key.contains('\n')) {
      throw const FormatException('Brak klucza własnego serwera.');
    }
    return {
      'Authorization': 'Bearer ' + key,
      'Accept': 'application/json',
      if (mime != null) 'Content-Type': mime,
    };
  }

  Future<Map<String, dynamic>> parse(http.Response response) async {
    if (response.statusCode == 401 || response.statusCode == 403) {
      throw const FormatException('Brak dostępu lub wymaganego potwierdzenia praw.');
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw FormatException('Serwer odmówił wykonania: HTTP ' +
        response.statusCode.toString());
    }
    final result = jsonDecode(utf8.decode(response.bodyBytes));
    if (result is! Map<String, dynamic>) {
      throw const FormatException('Nieprawidłowa odpowiedź serwera.');
    }
    return result;
  }

  Future<Map<String, dynamic>> call(String server, String secret,
      String operation, {Map<String, Object?>? payload}) async {
    final uri = url(server, operation);
    final result = payload == null
        ? await client.get(uri, headers: headers(secret))
            .timeout(const Duration(seconds: 30))
        : await client.post(uri, headers: headers(secret, mime: 'application/json'),
            body: jsonEncode(payload)).timeout(const Duration(seconds: 30));
    return parse(result);
  }

  Future<Map<String, dynamic>> upload(
      String server, String secret, File file, String mime) async {
    final size = await file.length();
    if (size < 12 || size > 160 * 1024 * 1024) {
      throw const FormatException('Maksymalny rozmiar pliku to 160 MiB.');
    }
    final request = http.StreamedRequest('POST', url(server, 'assets'));
    request.headers.addAll(headers(secret, mime: mime));
    request.contentLength = size;
    await request.sink.addStream(file.openRead());
    await request.sink.close();
    final streamed = await client.send(request).timeout(const Duration(minutes: 5));
    return parse(await http.Response.fromStream(streamed));
  }

  Future<File> download(String server, String secret, String id) async {
    if (!RegExp(r'^[a-f0-9]{32}$').hasMatch(id)) {
      throw const FormatException('Nieprawidłowy identyfikator renderu.');
    }
    final request = http.Request('GET', url(server, 'jobs/' + id + '/file'));
    request.headers.addAll(headers(secret));
    final response = await client.send(request).timeout(const Duration(seconds: 30));
    if (response.statusCode != 200) {
      throw FormatException('Film nie jest gotowy (HTTP ' +
        response.statusCode.toString() + ').');
    }
    final folder = await getApplicationDocumentsDirectory();
    final file = File(folder.path + '/unthinkable-film-' + id + '.mp4');
    final output = file.openWrite();
    var size = 0;
    try {
      await for (final chunk in response.stream) {
        size += chunk.length;
        if (size > 3 * 1024 * 1024 * 1024) {
          throw const FormatException('Zbyt duży plik MP4.');
        }
        output.add(chunk);
      }
      await output.flush();
      await output.close();
      if (size < 12) throw const FormatException('Pusty film.');
      return file;
    } on Object {
      await output.close();
      if (await file.exists()) await file.delete();
      rethrow;
    }
  }
}

/// Function-first prototype. The owner will provide final artwork/layout.
class OwnFilmStudioScreen extends StatefulWidget {
  const OwnFilmStudioScreen({super.key, this.api});
  final OwnFilmClient? api;
  @override
  State<OwnFilmStudioScreen> createState() => _OwnFilmStudioScreenState();
}

class _OwnFilmStudioScreenState extends State<OwnFilmStudioScreen> {
  late final OwnFilmClient api;
  final server = TextEditingController();
  final secret = TextEditingController();
  final title = TextEditingController(text: 'Mój film');
  final duration = TextEditingController(text: '5');
  final shots = <Map<String, Object>>[];
  String? songId, jobId, jobState, message, error;
  Map<String, dynamic>? capability;
  bool rights = false, busy = false;

  @override
  void initState() {
    super.initState();
    api = widget.api ?? OwnFilmClient();
  }

  @override
  void dispose() {
    server.dispose(); secret.clear(); secret.dispose();
    title.dispose(); duration.dispose(); api.close(); super.dispose();
  }

  Future<void> run(Future<void> Function() action) async {
    if (busy) return;
    setState(() { busy = true; error = null; message = null; });
    try {
      await action();
    } on Object catch (e) {
      if (mounted) setState(() => error = e is FormatException ?
          e.message : 'Nie udało się wykonać zadania naszego studia.');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> checkEngine() => run(() async {
    final result = await api.call(server.text, secret.text, 'capabilities');
    if (mounted) setState(() => capability = result);
  });

  Future<void> importMedia(bool isSong) => run(() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: isSong ? ['mp3', 'wav'] : ['mp4', 'png', 'jpg', 'jpeg'],
    );
    if (result == null || result.files.isEmpty) return;
    final item = result.files.single;
    if (item.path == null) throw const FormatException('Brak dostępu do pliku.');
    final ext = (item.extension ?? '').toLowerCase();
    final mime = switch (ext) {
      'mp4' => 'video/mp4',
      'mp3' => 'audio/mpeg',
      'wav' => 'audio/wav',
      'jpg' || 'jpeg' => 'image/jpeg',
      'png' => 'image/png',
      _ => throw const FormatException('Nieobsługiwany format.'),
    };
    final seconds = int.tryParse(duration.text.trim());
    if (!isSong && (seconds == null || seconds < 1 || seconds > 3600)) {
      throw const FormatException('Czas ujęcia: 1–3600 sekund.');
    }
    final saved = await api.upload(server.text, secret.text, File(item.path!), mime);
    final id = saved['asset_id'];
    if (id is! String) throw const FormatException('Nieprawidłowy zasób.');
    if (mounted) setState(() {
      if (isSong) {
        songId = id;
      } else {
        shots.add({'asset_id': id, 'name': item.name,
          'duration_seconds': seconds!});
      }
      message = 'Dodano materiał: ' + item.name;
    });
  });

  Future<void> render() => run(() async {
    if (shots.isEmpty || title.text.trim().isEmpty || !rights) {
      throw const FormatException('Dodaj ujęcia i zatwierdź prawa do mediów.');
    }
    final result = await api.call(server.text, secret.text, 'timeline/render',
      payload: {
        'title': title.text.trim(),
        'shots': shots,
        if (songId != null) 'soundtrack_asset_id': songId,
        'output_width': 1280,
        'fps': 24,
        'confirm_media_rights': rights,
      });
    if (mounted) setState(() {
      jobId = result['job_id']?.toString();
      jobState = result['status']?.toString();
      message = 'Wysłano do własnego renderera FFmpeg.';
    });
  });

  Future<void> refresh() => run(() async {
    if (jobId == null) return;
    final result = await api.call(server.text, secret.text, 'jobs/' + jobId!);
    if (mounted) setState(() => jobState = result['status']?.toString());
  });

  Future<void> download() => run(() async {
    if (jobId == null || jobState != 'completed') {
      throw const FormatException('Render jeszcze się nie zakończył.');
    }
    final file = await api.download(server.text, secret.text, jobId!);
    if (mounted) setState(() => message = 'Zapisano MP4: ' + file.path);
  });

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Unthinkable Film Studio')),
    body: SafeArea(child: ListView(padding: const EdgeInsets.all(16), children: [
      Text('Nasze Studio Filmowe', style: Theme.of(context).textTheme.headlineSmall),
      const Text('Własny silnik montażu i własna infrastruktura. '
        'Nie wymaga konta ani kredytów zewnętrznej platformy.'),
      const SizedBox(height: 14),
      TextField(key: const Key('own_film_server'), controller: server,
        decoration: const InputDecoration(labelText: 'Serwer Unthinkable AI HTTPS')),
      TextField(key: const Key('own_film_key'), controller: secret,
        obscureText: true, enableSuggestions: false, autocorrect: false,
        decoration: const InputDecoration(labelText: 'Klucz naszego serwera')),
      TextButton.icon(key: const Key('own_film_capabilities'),
        onPressed: busy ? null : checkEngine,
        icon: const Icon(Icons.settings_outlined),
        label: const Text('Sprawdź nasz silnik')),
      if (capability != null) Text('FFmpeg: ' +
        (capability!['local_ffmpeg_ready'] == true ? 'dostępny' : 'brak') +
        ' • magazyn: ' +
        (capability!['private_storage_ready'] == true ? 'dostępny' : 'brak')),
      const Divider(height: 28),
      TextField(key: const Key('own_film_title'), controller: title,
        decoration: const InputDecoration(labelText: 'Tytuł filmu')),
      TextField(key: const Key('own_film_duration'), controller: duration,
        keyboardType: TextInputType.number,
        decoration: const InputDecoration(labelText: 'Czas następnego ujęcia (s)')),
      OutlinedButton.icon(key: const Key('own_film_add_shot'),
        onPressed: busy ? null : () => importMedia(false),
        icon: const Icon(Icons.video_library_outlined),
        label: const Text('Dodaj zdjęcie / MP4')),
      for (var i = 0; i < shots.length; i++)
        ListTile(
          title: Text(shots[i]['name'].toString()),
          subtitle: Text(shots[i]['duration_seconds'].toString() + ' sekund'),
          trailing: IconButton(icon: const Icon(Icons.delete_outline),
            onPressed: busy ? null : () => setState(() => shots.removeAt(i))),
        ),
      OutlinedButton.icon(key: const Key('own_film_add_mp3'),
        onPressed: busy ? null : () => importMedia(true),
        icon: const Icon(Icons.music_note_outlined),
        label: const Text('Dodaj MP3/WAV — teledysk')),
      if (songId != null) Text('Ścieżka muzyczna: dodana'),
      CheckboxListTile(key: const Key('own_film_rights'), value: rights,
        title: const Text('Mam prawo do użycia materiałów i odpowiednie zgody'),
        onChanged: busy ? null : (v) => setState(() => rights = v ?? false)),
      FilledButton.icon(key: const Key('own_film_render'),
        onPressed: busy || shots.isEmpty || !rights ? null : render,
        icon: const Icon(Icons.movie_creation_outlined),
        label: const Text('Renderuj MP4 we własnym studio')),
      if (jobId != null) ...[
        Text('Zadanie: ' + jobId! + ' • ' + (jobState ?? 'queued')),
        OutlinedButton(key: const Key('own_film_refresh'),
          onPressed: busy ? null : refresh, child: const Text('Sprawdź postęp')),
        if (jobState == 'completed') FilledButton(
          key: const Key('own_film_download'),
          onPressed: busy ? null : download, child: const Text('Zapisz gotowy MP4')),
      ],
      if (busy) const LinearProgressIndicator(),
      if (error != null) Text(error!, style: const TextStyle(color: Colors.orangeAccent)),
      if (message != null) SelectableText(message!),
      const SizedBox(height: 16),
      const Text('To działający montaż FFmpeg. Generator AI Wan/LTX/ODYN, '
        'awatarów, podmiana twarzy i automatyczny beat-sync wymagają '
        'odrębnych własnych modeli i workerów GPU.'),
    ])),
  );
}
