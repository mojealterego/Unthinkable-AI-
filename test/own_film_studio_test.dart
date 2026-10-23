import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:unthinkable_ai/features/video/own_film_studio_screen.dart';

void main() {
  test('Own studio uses our API and no external credits', () async {
    final api = OwnFilmClient(httpClient: MockClient((request) async {
      expect(request.url.toString(), 'https://film.example/api/film-studio/capabilities');
      expect(request.headers['Authorization'], 'Bearer own-key');
      return http.Response(jsonEncode({
        'provider': 'unthinkable_self_hosted',
        'local_ffmpeg_ready': true,
        'third_party_credits': false,
      }), 200);
    }));
    final data = await api.call('https://film.example', 'own-key', 'capabilities');
    expect(data['provider'], 'unthinkable_self_hosted');
    expect(data['third_party_credits'], false);
    api.close();
  });

  test('Reject public HTTP, embedded credentials and path traversal', () {
    final api = OwnFilmClient();
    expect(() => api.url('http://remote.example', 'capabilities'),
      throwsFormatException);
    expect(() => api.url('https://user:pass@remote.example', 'capabilities'),
      throwsFormatException);
    expect(() => api.url('https://film.example', '../etc/passwd'),
      throwsFormatException);
    expect(api.url('http://127.0.0.1:8081', 'capabilities').path,
      '/api/film-studio/capabilities');
    api.close();
  });

  testWidgets('Studio is ours with real engine controls', (tester) async {
    final api = OwnFilmClient(httpClient: MockClient((request) async =>
      http.Response('{}', 200)));
    await tester.pumpWidget(MaterialApp(home: OwnFilmStudioScreen(api: api)));
    await tester.pumpAndSettle();
    expect(find.text('Nasze Studio Filmowe'), findsOneWidget);
    expect(find.byKey(const Key('own_film_capabilities')), findsOneWidget);
    expect(find.textContaining('VisionStory'), findsNothing);
    api.close();
  });
}
