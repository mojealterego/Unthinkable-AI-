import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

/// Gateway bearer credential is ephemeral. VisionStory's actual API key is
/// configured only on the private backend, never inside an APK.
class VisionStoryGateway {
  VisionStoryGateway({http.Client? client})
      : _http = client ?? http.Client(), _ownsClient = client == null;

  final http.Client _http;
  final bool _ownsClient;
  void close() { if (_ownsClient) _http.close(); }

  Uri endpoint(String server, String path) {
    final url = Uri.tryParse(server.trim());
    if (url == null || url.scheme != 'https' || url.host.isEmpty ||
        url.userInfo.isNotEmpty || url.hasQuery || url.hasFragment ||
        (url.path.isNotEmpty && url.path != '/')) {
      throw const FormatException('Wymagany jest główny adres serwera HTTPS.');
    }
    if (!RegExp(r'^[a-zA-Z0-9/_-]+$').hasMatch(path)) {
      throw const FormatException('Nieprawidłowa ścieżka operacji.');
    }
    return url.replace(path: '/api/cinema/visionstory/' + path);
  }

  Map<String, String> headers(String secret) {
    final key = secret.trim();
    if (key.isEmpty || key.contains('\r') || key.contains('\n')) {
      throw const FormatException('Wymagany poprawny klucz gateway.');
    }
    return {'Authorization': 'Bearer ' + key,
      'Content-Type': 'application/json', 'Accept': 'application/json'};
  }

  Future<http.Response> _request({
    required String server, required String key, required String path,
    Map<String, Object?>? body, bool binary = false,
  }) async {
    final uri = endpoint(server, path);
    final h = headers(key);
    if (binary) h['Accept'] = 'audio/mpeg';
    try {
      return await (body == null
          ? _http.get(uri, headers: h)
          : _http.post(uri, headers: h, body: jsonEncode(body)))
          .timeout(Duration(seconds: body == null ? 25 : 210));
    } on TimeoutException {
      throw const VisionStoryGatewayError(
        'Przekroczono czas oczekiwania. Nie ponawiaj automatycznie płatnego zlecenia.');
    } on http.ClientException {
      throw const VisionStoryGatewayError('Błąd połączenia z backendem.');
    }
  }

  Future<Map<String, dynamic>> call({
    required String server, required String key, required String path,
    Map<String, Object?>? body,
  }) async {
    final reply = await _request(
      server: server, key: key, path: path, body: body);
    if (reply.statusCode == 401 || reply.statusCode == 403) {
      throw const VisionStoryGatewayError('Brak uprawnień lub zgody na tę operację.');
    }
    if (reply.statusCode < 200 || reply.statusCode >= 300) {
      throw VisionStoryGatewayError(
        'Błąd serwera HTTP ' + reply.statusCode.toString());
    }
    try {
      final value = jsonDecode(utf8.decode(reply.bodyBytes));
      if (value is! Map<String, dynamic>) throw const FormatException('JSON');
      return value;
    } on FormatException {
      throw const VisionStoryGatewayError('Nieprawidłowa odpowiedź JSON.');
    }
  }

  Future<List<int>> makeMp3({
    required String server, required String key,
    required String text, required String voiceId, String locale = 'pl-PL',
  }) async {
    if (text.trim().isEmpty || voiceId.trim().isEmpty) {
      throw const FormatException('Wpisz tekst oraz istniejący identyfikator głosu.');
    }
    final reply = await _request(
      server: server, key: key, path: 'speech/tts', binary: true,
      body: {
        'text': text,
        'voice_id': voiceId,
        'locale': locale,
        'confirmed_voice_rights': true,
        'approved_for_paid_generation': true,
      },
    );
    if (reply.statusCode != 200) {
      throw VisionStoryGatewayError(
        'Synteza MP3 nie powiodła się: HTTP ' + reply.statusCode.toString());
    }
    final bytes = reply.bodyBytes;
    final id3 = bytes.length >= 3 && bytes[0] == 73 &&
        bytes[1] == 68 && bytes[2] == 51;
    final frame = bytes.length >= 2 && bytes[0] == 255 &&
        (bytes[1] & 0xE0) == 0xE0;
    if (!id3 && !frame) {
      throw const VisionStoryGatewayError('Serwer nie zwrócił poprawnego MP3.');
    }
    return bytes;
  }
}

class VisionStoryGatewayError implements Exception {
  const VisionStoryGatewayError(this.message);
  final String message;
  @override String toString() => message;
}
