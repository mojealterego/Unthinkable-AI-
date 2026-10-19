import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';

/// Private Unthinkable gateway client. Never embeds VisionStory's provider key.
class VisionStoryApi {
  VisionStoryApi({http.Client? client}) : _http = client ?? http.Client(), _own = client == null;
  final http.Client _http;
  final bool _own;
  void dispose() { if (_own) _http.close(); }

  Uri _uri(String server, String path, [Map<String, String>? query]) {
    final uri = Uri.tryParse(server.trim());
    if (uri == null || uri.scheme != 'https' || uri.host.isEmpty ||
        uri.userInfo.isNotEmpty || uri.hasQuery || uri.hasFragment ||
        (uri.path.isNotEmpty && uri.path != '/')) {
      throw const FormatException('Wymagany główny adres serwera HTTPS.');
    }
    if (!RegExp(r'^[a-z0-9/-]+$').hasMatch(path) ||
        path.startsWith('/') || path.contains('//')) {
      throw const FormatException('Niedozwolona ścieżka.');
    }
    return uri.replace(path: '/api/cinema/visionstory/' + path,
        queryParameters: query != null && query.isNotEmpty ? query : null);
  }

  http.Request _request(String method, String server, String key, String path,
      [Map<String, Object?>? data, Map<String, String>? query]) {
    final apiKey = key.trim();
    if (apiKey.isEmpty || apiKey.contains('\r') || apiKey.contains('\n')) {
      throw const FormatException('Brak klucza własnego backendu.');
    }
    final req = http.Request(method, _uri(server, path, query));
    req.followRedirects = false;
    req.headers['Authorization'] = 'Bearer ' + apiKey;
    req.headers['Accept'] = 'application/json';
    if (data != null) {
      req.headers['Content-Type'] = 'application/json; charset=utf-8';
      req.body = jsonEncode(data);
    }
    return req;
  }

  Future<http.StreamedResponse> _send(http.Request request) async {
    try {
      final result = await _http.send(request).timeout(const Duration(seconds: 190));
      if (result.statusCode >= 300 && result.statusCode < 400) {
        throw const VisionStoryClientError('Przekierowania są niedozwolone.');
      }
      if (result.statusCode == 401 || result.statusCode == 403) {
        throw const VisionStoryClientError('Brak autoryzacji lub akceptacji operacji.');
      }
      if (result.statusCode < 200 || result.statusCode >= 300) {
        throw VisionStoryClientError('Serwer odmówił wykonania żądania: HTTP ' +
            result.statusCode.toString());
      }
      return result;
    } on TimeoutException {
      throw const VisionStoryClientError(
          'Timeout. Nie ponawiaj automatycznie płatnego żądania.');
    } on http.ClientException {
      throw const VisionStoryClientError('Błąd połączenia z backendem.');
    }
  }

  Future<Map<String, dynamic>> jsonRequest({
    required String server, required String key, required String route,
    String method = 'GET', Map<String, Object?>? payload,
    Map<String, String>? query,
  }) async {
    final response = await _send(_request(method, server, key, route, payload, query));
    final bytes = await response.stream.toBytes();
    if (bytes.length > 5 * 1024 * 1024) {
      throw const VisionStoryClientError('Odpowiedź przekroczyła limit 5 MB.');
    }
    try {
      final result = jsonDecode(utf8.decode(bytes));
      if (result is! Map<String, dynamic>) throw const FormatException();
      return result;
    } on FormatException {
      throw const VisionStoryClientError('Nieprawidłowy JSON odpowiedzi.');
    }
  }

  Future<Map<String, dynamic>> credits(String host, String key) =>
      jsonRequest(server: host, key: key, route: 'credits');
  Future<Map<String, dynamic>> models(String host, String key) =>
      jsonRequest(server: host, key: key, route: 'models');
  Future<Map<String, dynamic>> avatars(String host, String key, {bool isPublic = false}) =>
      jsonRequest(server: host, key: key,
          route: isPublic ? 'avatars/public' : 'avatars');
  Future<Map<String, dynamic>> voices(String host, String key, {String? locale}) =>
      jsonRequest(server: host, key: key, route: 'voices',
          query: locale != null && locale.isNotEmpty ? {'locale': locale} : null);

  Future<Map<String, dynamic>> submitText({
    required String host, required String key, required String avatarId,
    required String modelId, required String voiceId, required String text,
    required String requestId, required bool approved,
    String aspectRatio = '9:16', String resolution = '720p',
  }) => jsonRequest(server: host, key: key, route: 'talking-video', method: 'POST', payload: {
      'avatar_id': avatarId, 'model_id': modelId, 'voice_id': voiceId,
      'text': text, 'client_request_id': requestId,
      'aspect_ratio': aspectRatio, 'resolution': resolution,
      'approved_for_paid_generation': approved,
    });

  Future<Map<String, dynamic>> submitAudio({
    required String host, required String key, required String avatarId,
    required String modelId, required List<int> data, required String mime,
    required String requestId, required bool approved, required bool rights,
  }) {
    if (data.isEmpty || data.length > 8000000 ||
        !const {'audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/m4a'}.contains(mime)) {
      throw const FormatException('Audio musi być MP3/WAV/M4A do 8 MB.');
    }
    return jsonRequest(server: host, key: key, route: 'talking-video', method: 'POST',
        payload: {
          'avatar_id': avatarId, 'model_id': modelId,
          'client_request_id': requestId,
          'audio_script': {'inline_data': {
            'data': base64Encode(data), 'mime_type': mime,
          }},
          'confirmed_audio_rights': rights,
          'approved_for_paid_generation': approved,
        });
  }

  bool _validId(String id) => RegExp(r'^[a-zA-Z0-9_-]{3,160}$').hasMatch(id);
  Future<Map<String, dynamic>> status(String host, String key, String id) {
    if (!_validId(id)) throw const FormatException('Nieprawidłowy identyfikator filmu.');
    return jsonRequest(server: host, key: key, route: 'talking-video/' + id);
  }

  Future<Map<String, dynamic>> archive(String host, String key, String id) {
    if (!_validId(id)) throw const FormatException('Nieprawidłowy identyfikator filmu.');
    return jsonRequest(server: host, key: key,
        route: 'talking-video/' + id + '/archive', method: 'POST');
  }

  Future<Map<String, dynamic>> transcribe({
    required String host, required String key, required List<int> data,
    required String mime, required bool approved, required bool rights,
    bool srt = true, bool diarize = false,
  }) {
    if (data.isEmpty || data.length > 14000000 ||
        !const {'audio/mp3', 'audio/mpeg', 'audio/wav'}.contains(mime)) {
      throw const FormatException('Audio MP3/WAV do 14 MB.');
    }
    return jsonRequest(server: host, key: key, route: 'speech/transcribe',
        method: 'POST', payload: {
          'audio': {'inline_data': {
            'data': base64Encode(data), 'mime_type': mime,
          }},
          'srt': srt, 'diarize': diarize,
          'confirmed_audio_rights': rights,
          'approved_for_paid_generation': approved,
        });
  }

  Future<File> _save(
      http.StreamedResponse response, String name, int maxSize) async {
    final dir = await getApplicationDocumentsDirectory();
    final folder = Directory(dir.path + '/unthinkable/visionstory');
    await folder.create(recursive: true);
    final dst = File(folder.path + '/' + name);
    final tmp = File(dst.path + '.part');
    var total = 0;
    final output = tmp.openWrite();
    try {
      await for (final part in response.stream) {
        total += part.length;
        if (total > maxSize) {
          throw const VisionStoryClientError('Plik przekracza dozwolony rozmiar.');
        }
        output.add(part);
      }
      await output.flush();
      await output.close();
      if (total == 0) throw const VisionStoryClientError('Pusty plik.');
      if (await dst.exists()) await dst.delete();
      await tmp.rename(dst.path);
      return dst;
    } on Object {
      await output.close();
      if (await tmp.exists()) await tmp.delete();
      rethrow;
    }
  }

  Future<File> downloadMp4(String host, String key, String id) async {
    if (!_validId(id)) throw const FormatException('Nieprawidłowy identyfikator filmu.');
    final req = _request('GET', host, key, 'talking-video/' + id + '/file');
    req.headers['Accept'] = 'video/mp4';
    final stream = await _send(req);
    return _save(stream, 'visionstory_' + id + '.mp4', 120 * 1024 * 1024);
  }

  Future<File> synthesizeTts({
    required String host, required String key, required String text,
    required String voiceId, required bool approved, required bool rights,
  }) async {
    final req = _request('POST', host, key, 'speech/tts', {
      'text': text, 'voice_id': voiceId, 'locale': 'pl-PL',
      'confirmed_voice_rights': rights,
      'approved_for_paid_generation': approved,
    });
    req.headers['Accept'] = 'audio/mpeg';
    final response = await _send(req);
    return _save(response,
        'voice_' + DateTime.now().millisecondsSinceEpoch.toString() + '.mp3',
        20000000);
  }
}

class VisionStoryClientError implements Exception {
  const VisionStoryClientError(this.message);
  final String message;
  @override
  String toString() => message;
}
