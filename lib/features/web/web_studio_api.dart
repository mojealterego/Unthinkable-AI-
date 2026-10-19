import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'website_project.dart';

/// All remote operations use the owner's configured private HTTPS gateway.
class WebStudioApiClient {
  WebStudioApiClient({http.Client? client})
      : _client = client ?? http.Client(), _owns = client == null;
  final http.Client _client;
  final bool _owns;

  Uri _uri(String baseUrl, String path) {
    final url = Uri.tryParse(baseUrl.trim());
    if (url == null || url.scheme != 'https' || url.host.isEmpty ||
        url.userInfo.isNotEmpty || url.hasQuery || url.hasFragment ||
        (url.path.isNotEmpty && url.path != '/')) {
      throw const FormatException('Wymagany jest adres główny serwera HTTPS.');
    }
    return url.replace(path: path);
  }

  Future<http.Response> _post({
    required String baseUrl, required String apiKey, required String route,
    required Map<String, dynamic> body,
  }) async {
    final target = _uri(baseUrl, route);
    if (apiKey.trim().isEmpty || apiKey.contains('\n') || apiKey.contains('\r')) {
      throw const FormatException('Brak prawidłowego klucza API serwera.');
    }
    try {
      final response = await _client.post(
        target,
        headers: {
          'Authorization': 'Bearer ' + apiKey.trim(),
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode(body),
      ).timeout(const Duration(seconds: 35));
      if (response.statusCode < 200 || response.statusCode >= 300) {
        // Never display provider error bodies or authentication headers.
        throw WebStudioApiException('Serwer odrzucił żądanie (HTTP ' +
            response.statusCode.toString() + ').');
      }
      return response;
    } on TimeoutException {
      throw const WebStudioApiException('Przekroczono limit czasu połączenia.');
    } on http.ClientException {
      throw const WebStudioApiException('Nie można połączyć się z serwerem.');
    }
  }

  Future<Map<String, dynamic>> _json({
    required String baseUrl, required String apiKey,
    required String route, required Map<String, dynamic> body,
  }) async {
    final response = await _post(baseUrl: baseUrl, apiKey: apiKey,
      route: route, body: body);
    try {
      final result = jsonDecode(utf8.decode(response.bodyBytes));
      if (result is! Map<String, dynamic>) throw const FormatException('Invalid response');
      return result;
    } on FormatException {
      throw const WebStudioApiException('Nieprawidłowa odpowiedź JSON serwera.');
    }
  }

  Future<Map<String, dynamic>> scan({
    required String baseUrl, required String apiKey,
    required String url, required bool confirmed,
    int maxPages = 3,
  }) async {
    if (!confirmed) {
      throw const FormatException('Potwierdź uprawnienia do analizowanej witryny.');
    }
    final result = await _json(
      baseUrl: baseUrl, apiKey: apiKey, route: '/api/web/scrape',
      body: {'url': url, 'max_pages': maxPages, 'confirm_ownership': confirmed},
    );
    if (result['format'] != 'unthinkable-authorized-site-wrapper-v1' ||
        result['pages'] is! List || result['backend_extracted'] != false) {
      throw const WebStudioApiException('Nieobsługiwana odpowiedź skanera.');
    }
    return result;
  }

  Future<Map<String, dynamic>> wrap({
    required String baseUrl, required String apiKey,
    required Map<String, dynamic> snapshot,
  }) async {
    final result = await _json(baseUrl: baseUrl, apiKey: apiKey,
      route: '/api/web/wrapper', body: {'snapshot': snapshot});
    if (result['format'] != 'unthinkable-nocode-data-wrapper-v1' ||
        result['read_only'] != true) {
      throw const WebStudioApiException('Nieobsługiwana odpowiedź wrappera.');
    }
    return result;
  }

  Future<WebsiteProject> importToEditor({
    required String baseUrl, required String apiKey,
    required Map<String, dynamic> wrapper,
  }) async {
    final body = await _json(baseUrl: baseUrl, apiKey: apiKey,
      route: '/api/web/nocode/import-snapshot', body: {'wrapper': wrapper});
    return WebsiteProject.fromJson(body);
  }

  Future<List<int>> exportZip({
    required String baseUrl, required String apiKey,
    required WebsiteProject site,
  }) async {
    final response = await _post(baseUrl: baseUrl, apiKey: apiKey,
      route: '/api/web/nocode/export', body: site.toJson());
    if (response.bodyBytes.length < 4 ||
        response.bodyBytes[0] != 80 || response.bodyBytes[1] != 75) {
      throw const WebStudioApiException('Serwer nie zwrócił pliku ZIP.');
    }
    return response.bodyBytes;
  }

  void close() {
    if (_owns) _client.close();
  }
}

class WebStudioApiException implements Exception {
  const WebStudioApiException(this.message);
  final String message;
  @override
  String toString() => message;
}
