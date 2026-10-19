import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:unthinkable_ai/features/video/production_api.dart';
import 'package:unthinkable_ai/features/video/production_planner.dart';

Map<String, Object> shotlist() => {
  'format': 'unthinkable-film-shotlist-v1',
  'title': 'Film 123 minut',
  'masterPrompt': 'Powracająca postać',
  'shots': [
    {'id': 'a', 'name': 'Początek', 'durationSeconds': 7200, 'approved': true},
    {'id': 'b', 'name': 'Finał', 'durationSeconds': 200, 'approved': false},
  ],
};

Map<String, dynamic> validResponse() => {
  'format': 'unthinkable-production-plan-v1',
  'mode': 'planning_only',
  'generated_video': false,
  'project_title': 'Film 123 minut',
  'duration_seconds': 7400,
  'scenes': [
    {'id':'a','name':'Początek','duration_seconds':7200,'start_seconds':0,
     'end_seconds':7200,'actor_reference':'A1','approved':true},
    {'id':'b','name':'Finał','duration_seconds':200,'start_seconds':7200,
     'end_seconds':7400,'actor_reference':'A2','approved':false},
  ],
  'crew': List.generate(18, (index) => {'agent':'Specjalista','purpose':'Rola'}),
};

void main() {
  test('Authenticated call carries original scene lengths and approval state', () async {
    var requests = 0;
    final api = ProductionApiClient(client: MockClient((request) async {
      requests++;
      expect(request.url.toString(), 'https://cinema.example/api/cinema/projects/plan');
      expect(request.headers['Authorization'], 'Bearer unit-secret');
      final body = jsonDecode(request.body) as Map<String, dynamic>;
      expect(body['masterPrompt'], 'Powracająca postać');
      expect((body['shots'] as List)[1]['approved'], false);
      expect((body['shots'] as List)[0]['durationSeconds'], 7200);
      return http.Response.bytes(utf8.encode(jsonEncode(validResponse())), 200);
    }));
    final result = await api.planFilm(
      baseUrl:'https://cinema.example',apiKey:'unit-secret',project:shotlist());
    expect(requests, 1);
    expect(result['duration_seconds'], 7400);
    api.close();
  });

  test('Rejects insecure address and empty key before network access', () async {
    var requests = 0;
    final api = ProductionApiClient(client: MockClient((request) async {
      requests++;
      return http.Response('{}', 200);
    }));
    await expectLater(api.planFilm(
      baseUrl:'http://cinema.example',apiKey:'secret',project:shotlist()),
      throwsFormatException);
    await expectLater(api.planFilm(
      baseUrl:'https://cinema.example',apiKey:'',project:shotlist()),
      throwsFormatException);
    expect(requests, 0);
    api.close();
  });

  test('Rejects reordered, altered, or falsely rendered results', () async {
    final wrong = validResponse();
    (wrong['scenes'] as List)[1]['start_seconds'] = 7201;
    final api = ProductionApiClient(client: MockClient(
      (request) async => http.Response.bytes(utf8.encode(jsonEncode(wrong)), 200)));
    await expectLater(api.planFilm(
      baseUrl:'https://cinema.example',apiKey:'secret',project:shotlist()),
      throwsA(isA<ProductionApiException>()));
    api.close();
    final fakeRender = validResponse();
    fakeRender['generated_video'] = true;
    final fake = ProductionApiClient(client: MockClient(
      (request) async => http.Response.bytes(utf8.encode(jsonEncode(fakeRender)), 200)));
    await expectLater(fake.planFilm(
      baseUrl:'https://cinema.example',apiKey:'secret',project:shotlist()),
      throwsA(isA<ProductionApiException>()));
    fake.close();
  });

  testWidgets('Widget submits only on explicit user action', (tester) async {
    var requests = 0;
    final api = ProductionApiClient(client: MockClient((request) async {
      requests++;
      return http.Response.bytes(utf8.encode(jsonEncode(validResponse())), 200);
    }));
    await tester.pumpWidget(MaterialApp(
      home: ProductionPlannerScreen(project: shotlist(), client: api),
    ));
    expect(requests, 0);
    await tester.enterText(find.byKey(const Key('production_base_url')), 'https://cinema.example');
    await tester.enterText(find.byKey(const Key('production_api_key')), 'unit-secret');
    await tester.ensureVisible(find.byKey(const Key('request_production_plan')));
    await tester.tap(find.byKey(const Key('request_production_plan')));
    await tester.pumpAndSettle();
    expect(requests, 1);
    expect(find.text('Plan: Film 123 minut'), findsOneWidget);
    api.close();
  });
}
