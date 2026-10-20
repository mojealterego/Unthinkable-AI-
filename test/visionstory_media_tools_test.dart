import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:unthinkable_ai/features/video/visionstory_gateway.dart';
import 'package:unthinkable_ai/features/video/visionstory_media_tools_screen.dart';

void main() {
  test('The image catalog is gateway-authenticated and never sends provider secrets', () async {
    final client = VisionStoryGateway(client: MockClient((request) async {
      expect(request.url.toString(),
          'https://my-studio.example/api/cinema/visionstory/models/image');
      expect(request.headers['Authorization'], 'Bearer local-gateway');
      expect(request.headers.containsKey('X-API-Key'), false);
      return http.Response('{"models":[{"model_id":"sample_model"}]}', 200);
    }));
    final data = await client.call(
      server: 'https://my-studio.example', key: 'local-gateway',
      path: 'models/image',
    );
    expect((data['models'] as List).length, 1);
    client.close();
  });

  test('MP3 synthesis never starts without both explicit approvals', () async {
    var sent = false;
    final client = VisionStoryGateway(client: MockClient((request) async {
      sent = true;
      return http.Response('unsupported', 500);
    }));
    await expectLater(
      client.makeMp3(
        server: 'https://my-studio.example', key: 'local-gateway',
        text: 'Witaj', voiceId: 'voice1',
        approved: false, rights: true,
      ),
      throwsFormatException,
    );
    await expectLater(
      client.makeMp3(
        server: 'https://my-studio.example', key: 'local-gateway',
        text: 'Witaj', voiceId: 'voice1',
        approved: true, rights: false,
      ),
      throwsFormatException,
    );
    expect(sent, false);
    client.close();
  });

  test('Approved MP3 synthesis sends explicit flags to only the private backend', () async {
    final client = VisionStoryGateway(client: MockClient((request) async {
      expect(request.url.toString(),
        'https://my-studio.example/api/cinema/visionstory/speech/tts');
      final payload = jsonDecode(request.body) as Map<String, dynamic>;
      expect(payload['confirmed_voice_rights'], true);
      expect(payload['approved_for_paid_generation'], true);
      expect(request.headers['Authorization'], 'Bearer local-gateway');
      return http.Response.bytes([73, 68, 51, 3, 4], 200,
          headers: {'content-type': 'audio/mpeg'});
    }));
    final bytes = await client.makeMp3(
      server: 'https://my-studio.example', key: 'local-gateway',
      text: 'Witaj', voiceId: 'owned_voice_1',
      approved: true, rights: true,
    );
    expect(bytes.sublist(0, 3), [73, 68, 51]);
    client.close();
  });

  testWidgets('Media studio contains consented Avatar, Voice, Image and Asset panels',
      (tester) async {
    tester.view.physicalSize = const Size(800, 1800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const MaterialApp(home: VisionStoryMediaToolsScreen()));
    await tester.pumpAndSettle();
    expect(find.text('VisionStory — Awatary i multimedia'), findsOneWidget);
    expect(find.byKey(const Key('vs_media_host')), findsOneWidget);
    expect(find.byKey(const Key('vs_media_key')), findsOneWidget);
    expect(find.byKey(const Key('visionstory_create_avatar')), findsOneWidget);

    await tester.tap(find.text('Głosy').first);
    await tester.pumpAndSettle();
    expect(find.text('Klonowanie głosu wymaga zgody jego właściciela'), findsOneWidget);
    expect(find.byKey(const Key('visionstory_clone_voice')), findsOneWidget);

    await tester.tap(find.text('Obrazy').first);
    await tester.pumpAndSettle();
    expect(find.text('Dostępność modeli i ceny są zależne od Twojego konta.'), findsOneWidget);
    expect(find.byKey(const Key('visionstory_generate_image')), findsOneWidget);

    await tester.tap(find.text('Zasoby').first);
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('visionstory_assets_refresh')), findsOneWidget);
  });
}
