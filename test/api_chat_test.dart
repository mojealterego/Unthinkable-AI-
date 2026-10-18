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
}
