import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:unthinkable_ai/features/web_studio/nocode_engine.dart';
import 'package:unthinkable_ai/features/web_studio/web_studio_api.dart';
import 'package:unthinkable_ai/features/web_studio/web_studio_screen.dart';

void main() {
  test('NoCode generates actual escaped, responsive static HTML', () {
    final site = NoCodeSite(
      name: 'Moja marka',
      heading: 'Witaj <script>alert(1)</script>',
      description: 'Profesjonalna strona',
      blocks: const [
        SiteBlock(kind: SiteBlockKind.feature, text: 'Projektowanie',
          subtitle: 'Dla firm'),
        SiteBlock(kind: SiteBlockKind.button, text: 'Kontakt', link: '/kontakt'),
      ],
    );
    final html = site.toHtml();
    expect(html.startsWith('<!doctype html>'), true);
    expect(html.contains('&lt;script&gt;'), true);
    expect(html.contains('<script>'), false);
    expect(html.contains('Content-Security-Policy'), true);
    final recovered = NoCodeSite.fromJson(
      jsonDecode(jsonEncode(site.toJson())) as Map<String, dynamic>);
    expect(recovered.toHtml(), html);
  });

  test('NoCode blocks cannot inject dangerous protocols or HTML attributes', () {
    expect(
      () => NoCodeSite(name: 'X', heading: 'X', blocks: const [
        SiteBlock(kind: SiteBlockKind.button, text: 'Kliknij',
                  link: 'javascript:alert(1)'),
      ]).toHtml(),
      throwsFormatException,
    );
    expect(
      () => NoCodeSite(name: 'X', heading: 'X', blocks: const [
        SiteBlock(kind: SiteBlockKind.button, text: 'Kliknij',
                  link: 'https://example.com/" onclick="evil'),
      ]).toHtml(),
      throwsFormatException,
    );
  });

  test('Offline Wrapper creates a structured OpenAPI contract', () {
    final json = buildOpenApi('Moje API', const [
      WrapperOperation(name: 'get_projects', method: 'GET', path: '/projects',
        summary: 'Lista projektów'),
      WrapperOperation(name: 'create_project', method: 'POST', path: '/projects',
        summary: 'Nowy projekt'),
    ]);
    expect(json['openapi'], '3.1.0');
    final routes = json['paths'] as Map;
    expect((routes['/projects'] as Map).keys.toSet(), {'get', 'post'});
    expect(
      () => buildOpenApi('Niepoprawny', const [
        WrapperOperation(name: 'invalid', method: 'GET', path: '//example.org',
          summary: 'A'),
      ]),
      throwsFormatException,
    );
  });

  test('Scraper sends authorized HTTPS request and decodes Polish content', () async {
    final api = WebStudioApi(client: MockClient((request) async {
      expect(request.url.toString(),
        'https://studio.example/api/web-studio/scraper/inspect');
      expect(request.headers['Authorization'], 'Bearer test-key');
      final body = jsonDecode(request.body) as Map;
      expect(body['html'], '<h1>Przykładowa witryna</h1>');
      return http.Response.bytes(utf8.encode(jsonEncode({
        'title': 'Przykładowa', 'headings': [
          {'level': 'h1', 'text': 'Przykładowa witryna'},
        ], 'links': [], 'forms_count': 0,
      })), 200, headers: {'content-type': 'application/json; charset=utf-8'});
    }));
    final result = await api.inspect(
      server: 'https://studio.example', apiKey: 'test-key',
      html: '<h1>Przykładowa witryna</h1>',
    );
    expect(result['title'], 'Przykładowa');
    api.close();
  });

  test('Untrusted HTTP URLs and missing credentials never send requests', () async {
    var requests = 0;
    final api = WebStudioApi(client: MockClient((request) async {
      requests++;
      return http.Response('{}', 200);
    }));
    await expectLater(api.inspect(server: 'http://studio.example',
      apiKey: 'test-key', url: 'https://owned.example'), throwsFormatException);
    await expectLater(api.inspect(server: 'https://studio.example',
      apiKey: '', html: '<p>X</p>'), throwsFormatException);
    expect(requests, 0);
    api.close();
  });

  testWidgets('NoCode screen adds a feature, previews and persists it', (tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(const MaterialApp(home: WebStudioScreen()));
    await tester.pumpAndSettle();
    await tester.tap(find.text('NoCode WWW'));
    await tester.pumpAndSettle();
    expect(find.text('Website Creator NoCode'), findsOneWidget);
    await tester.enterText(find.byKey(const Key('web_site_name')), 'Nowa strona');
    tester.testTextInput.hide();
    await tester.pumpAndSettle();
    final editorList = find.ancestor(
      of: find.text('Website Creator NoCode'),
      matching: find.byType(Scrollable),
    ).first;
    await tester.scrollUntilVisible(
      find.byKey(const Key('nocode_block_title')),
      220,
      scrollable: editorList,
      maxScrolls: 30,
    );
    await tester.enterText(find.byKey(const Key('nocode_block_title')), 'Pierwsza usługa');
    await tester.ensureVisible(find.byKey(const Key('nocode_add_block')));
    await tester.tap(find.byKey(const Key('nocode_add_block')));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const Key('nocode_save')));
    await tester.tap(find.byKey(const Key('nocode_save')));
    await tester.pumpAndSettle();
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString('unthinkable.webstudio.nocode.v1');
    expect(saved, isNotNull);
    expect(saved, contains('Pierwsza usługa'));
    expect(saved, contains('Nowa strona'));
  });
}
