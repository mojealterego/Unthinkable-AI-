import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:unthinkable_ai/features/chat/api_chat.dart';

void main() {
  test('OpenAI-compatible endpoint is called with expected roles and token', () async {
    final client = CompatibleChatClient(client: MockClient((request) async {
      expect(request.url.toString(), 'https://example.com/v1/chat/completions');
      expect(request.headers['Authorization'], 'Bearer secret-for-test');
      final data = jsonDecode(request.body) as Map<String, dynamic>;
      expect(data['model'], 'test-model');
      expect((data['messages'] as List).last['content'], 'Cześć');
      return http.Response(jsonEncode({
        'choices': [{'message': {'role': 'assistant', 'content': 'Witaj'}}],
      }), 200);
    }));
    final result = await client.send(
      baseUrl: 'https://example.com/v1', model: 'test-model',
      apiKey: 'secret-for-test', messages: [const ChatTurn('user', 'Cześć')],
    );
    expect(result, 'Witaj');
    client.close();
  });

  test('Rejects insecure HTTP endpoints and missing API keys', () async {
    final client = CompatibleChatClient(client: MockClient((request) async {
      fail('Untrusted request should never be sent.');
    }));
    expect(
      () => client.send(baseUrl: 'http://example.com/v1', model: 'm',
        apiKey: 'key', messages: [const ChatTurn('user', 'Hej')]),
      throwsFormatException,
    );
    expect(
      () => client.send(baseUrl: 'https://example.com/v1', model: 'm',
        apiKey: '', messages: [const ChatTurn('user', 'Hej')]),
      throwsFormatException,
    );
    client.close();
  });
  test('Own local GGUF runtime works on loopback without provider credentials', () async {
    final client = CompatibleChatClient(client: MockClient((request) async {
      expect(request.url.toString(), 'http://127.0.0.1:8080/v1/chat/completions');
      expect(request.headers.containsKey('Authorization'), isFalse);
      final json = jsonDecode(request.body) as Map;
      expect(json['model'], 'my-uncensored-gguf');
      return http.Response(jsonEncode({
        'choices': [{'message': {'content': 'Cześć z lokalnego modelu'}}],
      }), 200);
    }));
    expect(await client.send(
      baseUrl: 'http://127.0.0.1:8080/v1', apiKey: '',
      model: 'my-uncensored-gguf',
      messages: [const ChatTurn('user', 'Hej')],
    ), 'Cześć z lokalnego modelu');
    client.close();
  });

  test('Discovers models from own loopback server without a cloud key', () async {
    final client = CompatibleChatClient(client: MockClient((request) async {
      expect(request.url.toString(), 'http://localhost:8080/v1/models');
      expect(request.headers.containsKey('Authorization'), isFalse);
      return http.Response(jsonEncode({
        'data': [{'id': 'my-model.gguf'}, {'id': 'abliterated-model.gguf'}],
      }), 200);
    }));
    final discovered = await client.discoverModels(
      baseUrl: 'http://localhost:8080/v1', apiKey: '',
    );
    expect(discovered, ['my-model.gguf', 'abliterated-model.gguf']);
    client.close();
  });

  test('Refuses plaintext remote hosts or unencrypted API credentials', () async {
    var sent = false;
    final client = CompatibleChatClient(client: MockClient((request) async {
      sent = true;
      return http.Response('{}', 200);
    }));
    for (final params in [
      ('http://192.168.1.4:8080/v1', ''),
      ('http://example.com/v1', ''),
      ('http://127.0.0.1:8080/v1', 'insecure-key'),
      ('https://remote.example/v1', ''),
      ('http://localhost:8080/v1', 'secret'),
    ]) {
      await expectLater(
        client.discoverModels(baseUrl: params.$1, apiKey: params.$2),
        throwsFormatException,
      );
    }
    expect(sent, isFalse);
    client.close();
  });

}
