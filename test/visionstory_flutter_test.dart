import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:unthinkable_ai/features/video/visionstory_api.dart';
import 'package:unthinkable_ai/features/video/visionstory_screen.dart';

void main() {
  test('Gateway only allows user-provided HTTPS server, never HTTP URLs', () async {
    var invoked = false;
    final client = VisionStoryApi(client: MockClient((request) async {
      invoked = true;
      return http.Response('{}', 200);
    }));
    await expectLater(client.credits('http://internal', 'key'), throwsFormatException);
    await expectLater(client.credits('https://user:password@studio.example', 'key'),
        throwsFormatException);
    await expectLater(client.credits('https://studio.example', ''),
        throwsFormatException);
    expect(invoked, false);
    client.dispose();
  });

  test('Discovery uses authenticated gateway and does not disclose provider key', () async {
    final client = VisionStoryApi(client: MockClient((request) async {
      expect(request.url.toString(),
          'https://studio.example/api/cinema/visionstory/models');
      expect(request.headers['Authorization'], 'Bearer gateway-key');
      expect(request.followRedirects, false);
      return http.Response('{"models":[{"model_id":"vs_character_v4"}]}', 200);
    }));
    final result = await client.models('https://studio.example', 'gateway-key');
    expect((result['models'] as List).first['model_id'], 'vs_character_v4');
    client.dispose();
  });

  test('Text avatar submission preserves stable request id and approval state', () async {
    final client = VisionStoryApi(client: MockClient((request) async {
      final value = jsonDecode(request.body) as Map<String, dynamic>;
      expect(request.method, 'POST');
      expect(value['client_request_id'], 'cinema_1234567');
      expect(value['approved_for_paid_generation'], true);
      expect(value['avatar_id'], 'avatarA');
      expect(value['model_id'], 'modelA');
      expect(value['text'], 'Przykładowe zdanie.');
      return http.Response('{"video_id":"video_123"}', 200);
    }));
    final response = await client.submitText(
      host: 'https://studio.example', key: 'gateway-key',
      avatarId: 'avatarA', modelId: 'modelA', voiceId: 'voiceA',
      text: 'Przykładowe zdanie.', requestId: 'cinema_1234567',
      approved: true,
    );
    expect(response['video_id'], 'video_123');
    client.dispose();
  });

  test('Audio submit validates format and size before billable request', () async {
    var requests = 0;
    final client = VisionStoryApi(client: MockClient((request) async {
      requests++;
      return http.Response('{}', 200);
    }));
    expect(() => client.submitAudio(
      host: 'https://studio.example', key: 'gateway-key',
      avatarId: 'avatar', modelId: 'model',
      data: [1, 2], mime: 'application/json',
      requestId: 'cinema_1234567', approved: true, rights: true,
    ), throwsFormatException);
    expect(requests, 0);
    client.dispose();
  });

  test('Invalid job identifiers cannot become API path injections', () async {
    var invoked = false;
    final client = VisionStoryApi(client: MockClient((request) async {
      invoked = true;
      return http.Response('{}', 200);
    }));
    expect(() => client.status(
      'https://studio.example', 'gateway-key', '../private'
    ), throwsFormatException);
    expect(invoked, false);
    client.dispose();
  });

  testWidgets('Film UI exposes catalog, render jobs and speech panels',
      (tester) async {
    SharedPreferences.setMockInitialValues({});
    final api = VisionStoryApi(client: MockClient((request) async {
      return http.Response('{"remaining":100}', 200);
    }));
    await tester.pumpWidget(MaterialApp(home: VisionStoryScreen(api: api)));
    await tester.pumpAndSettle();
    expect(find.text('VisionStory • Studio Filmowe'), findsOneWidget);
    expect(find.byKey(const Key('vs_host')), findsOneWidget);
    expect(find.byKey(const Key('vs_key')), findsOneWidget);
    expect(find.text('Awatary'), findsOneWidget);
    expect(find.text('Zadania MP4'), findsOneWidget);
    expect(find.text('Audio / Napisy'), findsOneWidget);
    api.dispose();
  });
}
