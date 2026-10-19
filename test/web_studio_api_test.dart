import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:unthinkable_ai/features/web/web_studio_api.dart';
import 'package:unthinkable_ai/features/web/web_studio_screen.dart';

void main() {
  test('Scanner requires HTTPS, explicit ownership and a real gateway token', () async {
    var calls = 0;
    final api = WebStudioApiClient(client: MockClient((req) async {
      calls++;
      return http.Response('{}', 200);
    }));
    await expectLater(api.scan(
      baseUrl: 'http://example.org', apiKey: 'abc', url: 'https://owner.org',
      confirmed: true,
    ), throwsFormatException);
    await expectLater(api.scan(
      baseUrl: 'https://example.org', apiKey: 'abc', url: 'https://owner.org',
      confirmed: false,
    ), throwsFormatException);
    expect(calls, 0);
    api.close();
  });

  test('Wrapper and import return strongly validated NoCode structures', () async {
    final api = WebStudioApiClient(client: MockClient((req) async {
      expect(req.headers['Authorization'], 'Bearer unit-key');
      if (req.url.path.endsWith('/wrapper')) {
        return http.Response.bytes(utf8.encode(jsonEncode({
          'format': 'unthinkable-nocode-data-wrapper-v1',
          'read_only': true, 'pages': [],
        })), 200);
      }
      return http.Response.bytes(utf8.encode(jsonEncode({
        'format': 'unthinkable-nocode-website-v1',
        'name': 'Strona', 'theme': 'midnight', 'tagline': '',
        'pages': [{'slug':'index','title':'Start',
                   'sections':[{'type':'hero','heading':'Witaj'}]}],
      })), 200);
    }));
    final wrapper = await api.wrap(baseUrl: 'https://gateway.example',
      apiKey: 'unit-key',
      snapshot: {'format':'unthinkable-authorized-site-wrapper-v1','pages':[]});
    final editor = await api.importToEditor(baseUrl: 'https://gateway.example',
      apiKey: 'unit-key', wrapper: wrapper);
    expect(editor.pages.length, 1);
    expect(editor.pages.first.sections.first.heading, 'Witaj');
    api.close();
  });

  testWidgets('Website studio provides all three module entry tabs', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: WebStudioScreen()));
    await tester.pumpAndSettle();
    expect(find.text('Website Studio'), findsOneWidget);
    expect(find.text('Scraper'), findsOneWidget);
    expect(find.text('Wrapper'), findsOneWidget);
    expect(find.text('NoCode'), findsOneWidget);
    expect(find.byKey(const Key('web_scan_button')), findsOneWidget);
  });
}
