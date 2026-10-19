import 'dart:convert';

class WebsiteSection {
  WebsiteSection({required this.type, required this.heading, this.body = '',
    List<String>? items, this.buttonLabel = '', this.buttonUrl = ''})
      : items = items ?? [];
  String type;
  String heading;
  String body;
  List<String> items;
  String buttonLabel;
  String buttonUrl;

  Map<String, dynamic> toJson() => {
    'type': type, 'heading': heading, 'body': body, 'items': items,
    'button_label': buttonLabel, 'button_url': buttonUrl,
  };

  factory WebsiteSection.fromJson(Map<String, dynamic> raw) => WebsiteSection(
    type: raw['type'] as String? ?? 'text',
    heading: raw['heading'] as String? ?? 'Sekcja',
    body: raw['body'] as String? ?? '',
    items: (raw['items'] as List? ?? []).map((x) => x.toString()).toList(),
    buttonLabel: raw['button_label'] as String? ?? '',
    buttonUrl: raw['button_url'] as String? ?? '',
  );
}

class WebsitePage {
  WebsitePage({required this.slug, required this.title, List<WebsiteSection>? sections})
      : sections = sections ?? [WebsiteSection(type: 'hero', heading: title)];
  String slug;
  String title;
  List<WebsiteSection> sections;

  Map<String, dynamic> toJson() => {
    'slug': slug, 'title': title,
    'sections': sections.map((x) => x.toJson()).toList(),
  };
  factory WebsitePage.fromJson(Map<String, dynamic> raw) => WebsitePage(
    slug: raw['slug'] as String? ?? '',
    title: raw['title'] as String? ?? '',
    sections: (raw['sections'] as List? ?? []).map(
      (x) => WebsiteSection.fromJson(Map<String, dynamic>.from(x as Map)),
    ).toList(),
  );
}

class WebsiteProject {
  WebsiteProject({this.name = 'Moja witryna', this.tagline = '', this.theme = 'midnight',
    List<WebsitePage>? pages})
      : pages = pages ?? [
          WebsitePage(slug: 'index', title: 'Start', sections: [
            WebsiteSection(type: 'hero', heading: 'Witamy',
              body: 'Twoja witryna bez pisania kodu.'),
          ]),
        ];
  String name;
  String tagline;
  String theme;
  final List<WebsitePage> pages;

  Map<String, dynamic> toJson() => {
    'format': 'unthinkable-nocode-website-v1',
    'name': name, 'tagline': tagline, 'theme': theme,
    'pages': pages.map((x) => x.toJson()).toList(),
  };

  factory WebsiteProject.fromJson(Map<String, dynamic> raw) {
    if (raw['format'] != 'unthinkable-nocode-website-v1') {
      throw const FormatException('Nieobsługiwany format projektu.');
    }
    final list = raw['pages'];
    if (list is! List || list.isEmpty || list.length > 12) {
      throw const FormatException('Witryna musi mieć od 1 do 12 stron.');
    }
    final pages = list.map((x) =>
      WebsitePage.fromJson(Map<String, dynamic>.from(x as Map))).toList();
    final ids = pages.map((x) => x.slug).toList();
    if (!ids.contains('index') || ids.toSet().length != ids.length ||
        ids.any((x) => x != 'index' &&
          !RegExp(r'^[a-z][a-z0-9-]{0,47}$').hasMatch(x)) ||
        pages.any((x) => x.sections.isEmpty || x.sections.length > 35 ||
          x.sections.any((s) => !['hero','text','features','cta','contact'].contains(s.type)))) {
      throw const FormatException('Nieprawidłowe strony lub sekcje.');
    }
    return WebsiteProject(
      name: raw['name'] as String? ?? 'Moja witryna',
      tagline: raw['tagline'] as String? ?? '',
      theme: raw['theme'] as String? ?? 'midnight',
      pages: pages,
    );
  }

  static String escapeHtml(String input) => input
      .replaceAll('&', '&amp;').replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;').replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');

  static bool safeLink(String url) {
    if (url.isEmpty) return true;
    if (url.startsWith('/') && !url.startsWith('//') &&
        !url.contains('\\') && !url.contains('\n')) return true;
    final uri = Uri.tryParse(url);
    if (uri == null) return false;
    if (uri.scheme == 'https' && uri.host.isNotEmpty && uri.userInfo.isEmpty) return true;
    return RegExp(r'^mailto:[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,20}$')
        .hasMatch(url);
  }

  String renderHtml(WebsitePage page) {
    final bg = theme == 'light' ? '#f7f7fc' : '#0b0b11';
    final fg = theme == 'light' ? '#151520' : '#f6f3ff';
    final accent = theme == 'gold' ? '#d4af37' : '#9b83ff';
    final nav = pages.map((p) =>
      '<a href="' + (p.slug == 'index' ? 'index.html' : p.slug + '.html') + '">' +
      escapeHtml(p.title) + '</a>').join(' ');
    final sections = page.sections.map((s) {
      final tag = s.type == 'hero' ? 'h1' : 'h2';
      final items = s.type == 'features'
          ? '<ul>' + s.items.map((x) => '<li>' + escapeHtml(x) + '</li>').join() + '</ul>'
          : '';
      final button = s.buttonLabel.isNotEmpty && safeLink(s.buttonUrl) &&
          s.buttonUrl.isNotEmpty
          ? '<a class="button" href="' + escapeHtml(s.buttonUrl) + '">' +
              escapeHtml(s.buttonLabel) + '</a>'
          : '';
      return '<section><' + tag + '>' + escapeHtml(s.heading) + '</' + tag + '>' +
          '<p>' + escapeHtml(s.body).replaceAll('\n', '<br>') + '</p>' + items + button +
          '</section>';
    }).join();
    return '<!doctype html><html lang="pl"><head><meta charset="utf-8">' +
      '<meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<meta name="referrer" content="no-referrer">' +
      '<title>' + escapeHtml(page.title) + ' — ' + escapeHtml(name) + '</title>' +
      '<meta name="description" content="' + escapeHtml(tagline) + '">' +
      '<style>body{background:' + bg + ';color:' + fg + ';font:16px/1.6 system-ui,' +
      'sans-serif;margin:0}header,section,footer{padding:30px;max-width:960px;' +
      'margin:auto}a{color:' + accent + '}header{display:flex;gap:20px;' +
      'justify-content:space-between;flex-wrap:wrap}nav{display:flex;gap:15px}' +
      'section{padding-top:60px;padding-bottom:60px;border-bottom:1px solid #4446}' +
      'h1{font-size:clamp(32px,6vw,65px)}h2{font-size:clamp(25px,4vw,42px)}' +
      '.button{display:inline-block;background:' + accent + ';color:' + bg +
      ';padding:12px 24px;border-radius:10px;text-decoration:none}</style>' +
      '</head><body><header><strong>' + escapeHtml(name) +
      '</strong><nav>' + nav + '</nav></header><main>' + sections +
      '</main><footer>' + escapeHtml(name) + '</footer></body></html>';
  }

  String exportJson() => const JsonEncoder.withIndent('  ').convert(toJson());
}
