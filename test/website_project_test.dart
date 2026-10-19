import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:unthinkable_ai/features/web/website_project.dart';

void main() {
  test('NoCode document preserves pages, sections, navigation and metadata', () {
    final project = WebsiteProject(name: 'Firma', pages: [
      WebsitePage(slug: 'index', title: 'Start', sections: [
        WebsiteSection(type: 'hero', heading: 'Studio', body: 'Witaj'),
      ]),
      WebsitePage(slug: 'kontakt', title: 'Kontakt', sections: [
        WebsiteSection(type: 'contact', heading: 'Napisz'),
      ]),
    ]);
    final restored = WebsiteProject.fromJson(
      jsonDecode(project.exportJson()) as Map<String, dynamic>,
    );
    expect(restored.pages.length, 2);
    expect(restored.pages[1].slug, 'kontakt');
    expect(restored.renderHtml(restored.pages.first), contains('kontakt.html'));
  });

  test('HTML export escapes markup and disallows JavaScript links', () {
    final project = WebsiteProject(name: '<script>alert(1)</script>', pages: [
      WebsitePage(slug: 'index', title: 'Tytuł', sections: [
        WebsiteSection(type: 'text', heading: '<img src=x onerror=alert(1)>',
          body: 'A & B', buttonLabel: 'Click', buttonUrl: 'javascript:alert(1)'),
      ]),
    ]);
    final html = project.renderHtml(project.pages.first);
    expect(html, contains('&lt;script&gt;'));
    expect(html, isNot(contains('<script>alert(1)</script>')));
    expect(html, isNot(contains('href="javascript:')));
    expect(WebsiteProject.safeLink('https://example.org/path'), isTrue);
    expect(WebsiteProject.safeLink('javascript:alert(1)'), isFalse);
  });

  test('Rejects duplicate, invalid or missing pages', () {
    final raw = WebsiteProject().toJson();
    raw['pages'] = [];
    expect(() => WebsiteProject.fromJson(raw), throwsFormatException);
    raw['pages'] = [
      {'slug': 'index', 'title': 'Start', 'sections': [{'type':'hero','heading':'X'}]},
      {'slug': 'index', 'title': 'Start2', 'sections': [{'type':'text','heading':'Y'}]},
    ];
    expect(() => WebsiteProject.fromJson(raw), throwsFormatException);
  });
}
