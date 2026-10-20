import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:unthinkable_ai/features/video/visionstory_gateway.dart';
import 'package:unthinkable_ai/features/video/visionstory_understanding_screen.dart';

void main() {
  test('Structured media request sends only to authorized private gateway',
      () async {
    final gateway = VisionStoryGateway(client: MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.toString(),
          'https://studio.example/api/cinema/visionstory/media/understand');
      expect(request.headers['Authorization'], 'Bearer gateway-test');
      expect(request.headers.containsKey('X-API-Key'), false);
      final payload = jsonDecode(request.body) as Map<String, dynamic>;
      expect(payload['confirmed_media_rights'], true);
      expect(payload['approved_for_paid_generation'], true);
      expect(payload['inputs'], [{'asset_id': 'asset_one'}]);
      expect(payload['schema']['type'], 'object');
      return http.Response(
        '{"output":{"subject":"miasto"},"usage":{"input_tokens":10,"output_tokens":4},'
        '"cost_credit":1}', 200);
    }));
    final output = await gateway.call(
      server: 'https://studio.example', key: 'gateway-test',
      path: 'media/understand',
      body: {
        'prompt': 'Opisz scenę',
        'inputs': [{'asset_id': 'asset_one'}],
        'schema': {
          'type': 'object',
          'properties': {'subject': {'type': 'string'}},
        },
        'confirmed_media_rights': true,
        'approved_for_paid_generation': true,
      },
    );
    expect(output['cost_credit'], 1);
    gateway.close();
  });

  testWidgets('Media understanding refuses request without consent',
      (tester) async {
    tester.view.physicalSize = const Size(800, 1800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var sent = 0;
    final gateway = VisionStoryGateway(client: MockClient((request) async {
      sent++;
      return http.Response('{}', 200);
    }));
    await tester.pumpWidget(MaterialApp(home: VisionStoryUnderstandingScreen(
      gateway: gateway, initialServer: 'https://studio.example',
      initialGatewayKey: 'gateway-test',
    )));
    await tester.pumpAndSettle();
    expect(find.text('VisionStory — Analiza mediów'), findsOneWidget);
    final submit = find.byKey(const Key('vs_understand_submit'));
    await tester.scrollUntilVisible(submit, 250,
        scrollable: find.byType(Scrollable).first);
    await tester.tap(submit);
    await tester.pumpAndSettle();
    expect(find.text('Potwierdź prawa do mediów i możliwy koszt.'),
        findsOneWidget);
    expect(sent, 0);
    gateway.close();
  });

  testWidgets('User confirms paid analysis and receives structured result',
      (tester) async {
    tester.view.physicalSize = const Size(800, 2100);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var sent = 0;
    final gateway = VisionStoryGateway(client: MockClient((request) async {
      sent++;
      final payload = jsonDecode(request.body) as Map<String, dynamic>;
      expect(payload['inputs'], [{'asset_id': 'asset_001'}]);
      return http.Response(
        '{"output":{"subject":"film","scene":"noc"},"usage":{"input_tokens":6,'
        '"output_tokens":5},"cost_credit":2}', 200);
    }));
    await tester.pumpWidget(MaterialApp(home: VisionStoryUnderstandingScreen(
      gateway: gateway, initialServer: 'https://studio.example',
      initialGatewayKey: 'gateway-test',
    )));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('vs_understand_assets')),
        'asset_001');
    tester.testTextInput.hide();
    await tester.pumpAndSettle();
    final rights = find.byKey(const Key('vs_understand_rights'));
    final paid = find.byKey(const Key('vs_understand_paid'));
    await tester.ensureVisible(rights);
    await tester.tap(rights);
    await tester.ensureVisible(paid);
    await tester.tap(paid);
    final submit = find.byKey(const Key('vs_understand_submit'));
    await tester.ensureVisible(submit);
    await tester.tap(submit);
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('vs_understand_confirm')), findsOneWidget);
    expect(sent, 0);
    await tester.tap(find.byKey(const Key('vs_understand_confirm')));
    await tester.pumpAndSettle();
    expect(sent, 1);
    await tester.ensureVisible(find.byKey(const Key('vs_understand_result')));
    expect(find.text('Koszt: 2 kredytów'), findsOneWidget);
    expect(find.textContaining('"subject": "film"'), findsWidgets);
    gateway.close();
  });
}
