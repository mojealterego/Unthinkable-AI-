import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class ChatTurn {
  const ChatTurn(this.role, this.content);
  final String role;
  final String content;

  Map<String, String> toJson() => {'role': role, 'content': content};
}

class CompatibleChatClient {
  CompatibleChatClient({http.Client? client}) : _client = client ?? http.Client();
  final http.Client _client;

  /// Loopback permits the user's own llama.cpp-compatible server without a key.
  /// Remote runtimes require HTTPS and a private owner-defined API key.
  Uri _endpoint(String baseUrl, String apiKey, String action) {
    final uri = Uri.tryParse(baseUrl.trim());
    if (uri == null || uri.host.isEmpty || uri.userInfo.isNotEmpty ||
        uri.hasQuery || uri.hasFragment ||
        !const {'http', 'https'}.contains(uri.scheme)) {
      throw const FormatException('Nieprawidłowy adres serwera modeli.');
    }
    final local = uri.host == 'localhost' ||
        uri.host == '127.0.0.1' || uri.host == '::1';
    if (uri.scheme == 'http' && !local) {
      throw const FormatException('HTTP tylko lokalnie; zdalny silnik wymaga HTTPS.');
    }
    if (uri.scheme == 'http' && apiKey.trim().isNotEmpty) {
      throw const FormatException('Nie wysyłaj klucza API przez HTTP.');
    }
    if (uri.scheme == 'https' && apiKey.trim().isEmpty) {
      throw const FormatException('Zdalny serwer HTTPS wymaga klucza dostępu.');
    }
    if (apiKey.contains('\r') || apiKey.contains('\n')) {
      throw const FormatException('Nieprawidłowy klucz API.');
    }
    var path = uri.path;
    if (path.endsWith('/')) path = path.substring(0, path.length - 1);
    if (path.endsWith('/chat/completions')) {
      path = path.substring(0, path.length - '/chat/completions'.length);
    } else if (path.endsWith('/models')) {
      path = path.substring(0, path.length - '/models'.length);
    }
    return uri.replace(path: path + '/' + action);
  }

  Map<String, String> _headers(String key) => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    if (key.trim().isNotEmpty) 'Authorization': 'Bearer ' + key.trim(),
  };

  Future<List<String>> discoverModels({
    required String baseUrl,
    required String apiKey,
  }) async {
    final endpoint = _endpoint(baseUrl, apiKey, 'models');
    final response = await _client.get(
      endpoint, headers: _headers(apiKey),
    ).timeout(const Duration(seconds: 20));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('Serwer modeli zwrócił HTTP ' + response.statusCode.toString());
    }
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (decoded is! Map || decoded['data'] is! List) {
      throw const FormatException('Serwer nie obsługuje GET /models.');
    }
    final models = <String>{};
    for (final record in decoded['data'] as List) {
      if (record is Map && record['id'] is String &&
          (record['id'] as String).isNotEmpty) {
        models.add(record['id'] as String);
      }
    }
    return models.toList();
  }

  Future<String> send({
    required String baseUrl,
    required String apiKey,
    required String model,
    required List<ChatTurn> messages,
  }) async {
    final endpoint = _endpoint(baseUrl, apiKey, 'chat/completions');
    if (model.trim().isEmpty || messages.isEmpty) {
      throw const FormatException('Wybierz uruchomiony model i wpisz wiadomość.');
    }
    if (messages.length > 64 || messages.any((m) =>
        !const {'system', 'user', 'assistant'}.contains(m.role) ||
        m.content.length > 100000)) {
      throw const FormatException('Nieprawidłowa historia rozmowy.');
    }
    final response = await _client.post(
      endpoint,
      headers: _headers(apiKey),
      body: jsonEncode({
        'model': model.trim(),
        'messages': messages.map((m) => m.toJson()).toList(),
        'stream': false,
      }),
    ).timeout(const Duration(seconds: 90));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('Serwer modeli zwrócił HTTP ' + response.statusCode.toString());
    }
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException('Nieprawidłowa odpowiedź serwera.');
    }
    final choices = decoded['choices'];
    if (choices is! List || choices.isEmpty || choices.first is! Map) {
      throw const FormatException('Serwer nie zwrócił odpowiedzi modelu.');
    }
    final message = (choices.first as Map)['message'];
    if (message is! Map || message['content'] is! String) {
      throw const FormatException('Serwer nie zwrócił tekstu.');
    }
    return message['content'] as String;
  }

  void close() => _client.close();
}

class ApiChatScreen extends StatefulWidget {
  const ApiChatScreen({super.key});

  @override
  State<ApiChatScreen> createState() => _ApiChatScreenState();
}

class _ApiChatScreenState extends State<ApiChatScreen> {
  final _url = TextEditingController(text: 'http://127.0.0.1:8080/v1');
  final _model = TextEditingController();
  final _key = TextEditingController();
  final _prompt = TextEditingController();
  final _client = CompatibleChatClient();
  final _messages = <ChatTurn>[];
  bool _busy = false;
  String? _error;
  List<String> _availableModels = const [];

  Future<void> _discover() async {
    if (_busy) return;
    setState(() { _busy = true; _error = null; });
    try {
      final models = await _client.discoverModels(
        baseUrl: _url.text, apiKey: _key.text,
      );
      if (!mounted) return;
      setState(() {
        _availableModels = models;
        if (models.isNotEmpty && !models.contains(_model.text)) {
          _model.text = models.first;
        }
      });
    } on Object {
      if (mounted) setState(() => _error =
          'Nie udało się wykryć modeli. Uruchom własny serwer GGUF.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _send() async {
    if (_busy || _prompt.text.trim().isEmpty) return;
    final user = ChatTurn('user', _prompt.text.trim());
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final answer = await _client.send(
        baseUrl: _url.text, apiKey: _key.text, model: _model.text,
        messages: [..._messages, user],
      );
      if (!mounted) return;
      setState(() {
        _messages.add(user);
        _messages.add(ChatTurn('assistant', answer));
        _prompt.clear();
      });
    } on Object catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  void dispose() {
    _url.dispose();
    _model.dispose();
    _key.clear();
    _key.dispose();
    _prompt.dispose();
    _client.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Czat z własnym modelem')),
    body: SafeArea(child: Padding(padding: const EdgeInsets.all(12), child: Column(children: [
      TextField(key: const Key('api_base_url'), controller: _url,
        keyboardType: TextInputType.url,
        decoration: const InputDecoration(labelText: 'Mój silnik GGUF — localhost lub HTTPS')),
      Row(children: [
        Expanded(child: TextField(key: const Key('api_model'), controller: _model,
          decoration: const InputDecoration(labelText: 'ID mojego modelu'))),
        const SizedBox(width: 10),
        Expanded(child: TextField(key: const Key('api_key'), controller: _key,
          obscureText: true,
          decoration: const InputDecoration(labelText: 'Klucz tylko dla HTTPS'))),
      ]),
      OutlinedButton.icon(
        key: const Key('discover_local_models'),
        onPressed: _busy ? null : _discover,
        icon: const Icon(Icons.memory_outlined),
        label: const Text('Wykryj moje modele'),
      ),
      if (_availableModels.isNotEmpty)
        DropdownButton<String>(
          value: _availableModels.contains(_model.text) ? _model.text : null,
          hint: const Text('Wybierz dostępny model'),
          isExpanded: true,
          items: _availableModels.map((name) =>
              DropdownMenuItem(value: name, child: Text(name))).toList(),
          onChanged: (v) => setState(() => _model.text = v ?? _model.text),
        ),
      const SizedBox(height: 8),
      const Text('Domyślnie: GGUF przez serwer działający na tym telefonie (np. llama.cpp). '
        'Bez zewnętrznego konta ani klucza. Własny zdalny serwer wymaga HTTPS i dostępu.', style: TextStyle(fontSize: 12)),
      if (_error != null) Text(_error!, style: const TextStyle(color: Colors.orangeAccent)),
      const Divider(),
      Expanded(child: ListView.builder(
        itemCount: _messages.length,
        itemBuilder: (context, i) {
          final m = _messages[i];
          return Align(
            alignment: m.role == 'user' ? Alignment.centerRight : Alignment.centerLeft,
            child: Card(child: Padding(
              padding: const EdgeInsets.all(12),
              child: SelectableText('${m.role == 'user' ? 'Ty' : 'Model'}: ${m.content}'),
            )),
          );
        },
      )),
      TextField(key: const Key('chat_prompt'), controller: _prompt,
        minLines: 1, maxLines: 3,
        decoration: const InputDecoration(labelText: 'Wiadomość')),
      const SizedBox(height: 8),
      Row(children: [
        TextButton(onPressed: _busy ? null : () => setState(_messages.clear),
          child: const Text('Wyczyść rozmowę')),
        const Spacer(),
        FilledButton(
          key: const Key('send_chat'),
          onPressed: _busy ? null : _send,
          child: Text(_busy ? 'Oczekiwanie...' : 'Wyślij'),
        ),
      ]),
    ]))),
  );
}
