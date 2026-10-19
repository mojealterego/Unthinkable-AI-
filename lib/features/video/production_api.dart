import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

/// HTTPS-only client for a user-configured private production-planning server.
/// Credentials remain in the calling widget's memory and are never persisted.
class ProductionApiClient {
  ProductionApiClient({http.Client? client})
      : _client = client ?? http.Client(), _ownsClient = client == null;
  final http.Client _client;
  final bool _ownsClient;

  void close() {
    if (_ownsClient) _client.close();
  }

  Uri endpoint(String baseUrl) {
    final uri = Uri.tryParse(baseUrl.trim());
    if (uri == null || uri.scheme != 'https' || uri.host.isEmpty ||
        uri.userInfo.isNotEmpty || uri.hasQuery || uri.hasFragment ||
        (uri.path.isNotEmpty && uri.path != '/')) {
      throw const FormatException('Wymagany jest adres HTTPS serwera bez ścieżki i parametrów.');
    }
    return uri.replace(path: '/api/cinema/projects/plan');
  }

  Future<Map<String, dynamic>> planFilm({
    required String baseUrl,
    required String apiKey,
    required Map<String, Object> project,
  }) async {
    final url = endpoint(baseUrl);
    final key = apiKey.trim();
    if (key.isEmpty || key.contains('\n') || key.contains('\r')) {
      throw const FormatException('Brak poprawnego klucza API.');
    }
    if (project['format'] != 'unthinkable-film-shotlist-v1' ||
        project['shots'] is! List || (project['shots'] as List).isEmpty) {
      throw const FormatException('Najpierw dodaj sceny do projektu.');
    }

    late final http.Response reply;
    try {
      reply = await _client.post(
        url,
        headers: {
          'Authorization': 'Bearer ' + key,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode(project),
      ).timeout(const Duration(seconds: 30));
    } on TimeoutException {
      throw const ProductionApiException('Serwer nie odpowiedział w ciągu 30 sekund.');
    } on http.ClientException {
      throw const ProductionApiException('Nie można połączyć się z serwerem.');
    }

    if (reply.statusCode == 401 || reply.statusCode == 403) {
      throw const ProductionApiException('Odmowa dostępu. Sprawdź klucz API.');
    }
    if (reply.statusCode < 200 || reply.statusCode >= 300) {
      throw ProductionApiException('Błąd planowania HTTP ' + reply.statusCode.toString());
    }

    late final Map<String, dynamic> result;
    try {
      final json = jsonDecode(utf8.decode(reply.bodyBytes));
      if (json is! Map<String, dynamic>) throw const FormatException('Invalid result');
      result = json;
    } on FormatException {
      throw const ProductionApiException('Serwer nie zwrócił poprawnego JSON.');
    }

    if (result['format'] != 'unthinkable-production-plan-v1' ||
        result['mode'] != 'planning_only' ||
        result['generated_video'] != false ||
        result['scenes'] is! List ||
        result['crew'] is! List ||
        result['duration_seconds'] is! int) {
      throw const ProductionApiException('Nieobsługiwany kontrakt planowania.');
    }

    final shots = project['shots'] as List;
    final scenes = result['scenes'] as List;
    if (shots.length != scenes.length || (result['crew'] as List).length != 18) {
      throw const ProductionApiException('Serwer zwrócił niekompletny plan filmu.');
    }
    var cursor = 0;
    for (var i = 0; i < shots.length; i++) {
      final shot = shots[i];
      final scene = scenes[i];
      if (shot is! Map || scene is! Map ||
          shot['id'] != scene['id'] ||
          shot['durationSeconds'] != scene['duration_seconds'] ||
          scene['start_seconds'] != cursor) {
        throw const ProductionApiException('Serwer zmienił kolejność lub długość scen.');
      }
      cursor += shot['durationSeconds'] as int;
    }
    if (cursor != result['duration_seconds']) {
      throw const ProductionApiException('Czas scen nie zgadza się z czasem projektu.');
    }
    return result;
  }
}

class ProductionApiException implements Exception {
  const ProductionApiException(this.message);
  final String message;
  @override
  String toString() => message;
}
