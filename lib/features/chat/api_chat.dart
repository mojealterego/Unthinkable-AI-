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

  Future<String> send({
    required String baseUrl,
    required String apiKey,
    required String model,
    required List<ChatTurn> messages,
  }) async {
    final parsed = Uri.tryParse(baseUrl.trim());
    if (parsed == null || parsed.scheme != 'https' || parsed.host.isEmpty ||
        parsed.userInfo.isNotEmpty || parsed.hasQuery || parsed.hasFragment) {
      throw const FormatException('Adres API musi być poprawnym adresem HTTPS bez parametrów.');
    }
    if (apiKey.trim().isEmpty || model.trim().isEmpty || messages.isEmpty) {
      throw const FormatException('Wymagane: klucz API, model i wiadomość.');
    }
    if (messages.length > 64 || messages.any((m) =>
        !const {'system', 'user', 'assistant'}.contains(m.role) || m.content.length > 100000)) {
      throw const FormatException('Nieprawidłowa historia rozmowy.');
    }
    final basePath = parsed.path.endsWith('/') ? parsed.path.substring(0, parsed.path.length - 1) : parsed.path;
    final suffix = basePath.endsWith('/chat/completions') ? '' : '/chat/completions';
    final endpoint = parsed.replace(path: '$basePath$suffix');
    final response = await _client.post(
      endpoint,
      headers: {
        'Authorization': 'Bearer ${apiKey.trim()}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: jsonEncode({
        'model': model.trim(),
        'messages': messages.map((m) => m.toJson()).toList(),
        'stream': false,
      }),
    ).timeout(const Duration(seconds: 90));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      // Never surface request headers or provider error bodies; they may contain secrets.
      throw StateError('Dostawca API zwrócił HTTP ${response.statusCode}.');
    }
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (decoded is! Map<String, dynamic>) throw const FormatException('Nieprawidłowa odpowiedź API.');
    final choices = decoded['choices'];
    if (choices is! List || choices.isEmpty) throw const FormatException('API nie zwróciło odpowiedzi.');
    final first = choices.first;
    if (first is! Map<String, dynamic>) throw const FormatException('Błędny format odpowiedzi API.');
    final message = first['message'];
    if (message is! Map<String, dynamic> || message['content'] is! String) {
      throw const FormatException('Brak tekstu odpowiedzi w API.');
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
  final _url = TextEditingController(text: 'https://api.openai.com/v1');
  final _model = TextEditingController();
  final _key = TextEditingController();
  final _prompt = TextEditingController();
  final _client = CompatibleChatClient();
  final _messages = <ChatTurn>[];
  bool _busy = false;
  String? _error;

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
    appBar: AppBar(title: const Text('Czat API — OpenAI-compatible')),
    body: SafeArea(child: Padding(padding: const EdgeInsets.all(12), child: Column(children: [
      TextField(key: const Key('api_base_url'), controller: _url,
        keyboardType: TextInputType.url,
        decoration: const InputDecoration(labelText: 'Endpoint HTTPS (np. /v1)')),
      Row(children: [
        Expanded(child: TextField(key: const Key('api_model'), controller: _model,
          decoration: const InputDecoration(labelText: 'ID modelu dostawcy'))),
        const SizedBox(width: 10),
        Expanded(child: TextField(key: const Key('api_key'), controller: _key,
          obscureText: true,
          decoration: const InputDecoration(labelText: 'Klucz API'))),
      ]),
      const SizedBox(height: 8),
      const Text('Klucz pozostaje wyłącznie w pamięci tej sesji. Brak wysyłki bez naciśnięcia Wyślij.',
        style: TextStyle(fontSize: 12)),
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
