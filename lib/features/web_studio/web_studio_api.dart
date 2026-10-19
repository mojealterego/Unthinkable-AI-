import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'nocode_engine.dart';

/// Explicit authorization and HTTPS are required for every remote call.
class WebStudioApi {
  WebStudioApi({http.Client? client}) : _client = client ?? http.Client(),
    _ownsClient = client == null;
  final http.Client _client;
  final bool _ownsClient;
  void close() { if (_ownsClient) _client.close(); }

  Uri _endpoint(String server, String route) {
    final u = Uri.tryParse(server.trim());
    if (u == null || u.scheme != 'https' || u.host.isEmpty ||
        u.userInfo.isNotEmpty || u.hasQuery || u.hasFragment ||
        (u.path.isNotEmpty && u.path != '/')) {
      throw const FormatException('Wprowadź główny adres serwera HTTPS.');
    }
    return u.replace(path: '/api/web-studio/' + route);
  }

  Future<Map<String, dynamic>> request({
    required String server, required String apiKey,
    required String route, required Map<String, Object?> payload,
  }) async {
    final url = _endpoint(server, route);
    final key = apiKey.trim();
    if (key.isEmpty || key.contains('\n') || key.contains('\r')) {
      throw const FormatException('Wprowadź poprawny klucz API.');
    }
    late final http.Response response;
    try {
      response = await _client.post(url, headers: {
        'Authorization': 'Bearer ' + key,
        'Content-Type': 'application/json', 'Accept': 'application/json',
      }, body: jsonEncode(payload)).timeout(const Duration(seconds: 30));
    } on TimeoutException {
      throw const WebStudioException('Serwer nie odpowiedział w ciągu 30 sekund.');
    } on http.ClientException {
      throw const WebStudioException('Błąd połączenia z serwerem.');
    }
    if (response.statusCode == 401 || response.statusCode == 403) {
      throw const WebStudioException('Brak dostępu do serwera lub strony.');
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw WebStudioException('Serwer odrzucił operację HTTP ' +
        response.statusCode.toString());
    }
    try {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is! Map<String, dynamic>) throw const FormatException('Invalid response');
      return decoded;
    } on FormatException {
      throw const WebStudioException('Serwer zwrócił niepoprawny JSON.');
    }
  }

  Future<Map<String, dynamic>> inspect({
    required String server, required String apiKey,
    String url = '', String html = '',
  }) {
    if (html.trim().isEmpty && url.trim().isEmpty) {
      throw const FormatException('Podaj HTML lub URL.');
    }
    return request(
      server: server, apiKey: apiKey,
      route: html.trim().isEmpty ? 'scraper/fetch' : 'scraper/inspect',
      payload: html.trim().isEmpty ? {'url': url.trim()} : {'html': html},
    );
  }

  Future<Map<String, dynamic>> wrapper({
    required String server, required String apiKey,
    required String title, required List<WrapperOperation> operations,
  }) {
    buildOpenApi(title, operations);
    return request(
      server: server, apiKey: apiKey, route: 'wrapper/build',
      payload: {
        'title': title,
        'operations': operations.map((op) => {
          'operation_id': op.name, 'method': op.method,
          'path': op.path, 'summary': op.summary,
        }).toList(),
      },
    );
  }
}

class WebStudioException implements Exception {
  const WebStudioException(this.message);
  final String message;
  @override
  String toString() => message;
}
