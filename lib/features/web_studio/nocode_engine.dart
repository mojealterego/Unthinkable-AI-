import 'dart:convert';

enum SiteBlockKind { feature, paragraph, button }

class SiteBlock {
  const SiteBlock({required this.kind, required this.text, this.subtitle = '', this.link = ''});
  final SiteBlockKind kind;
  final String text;
  final String subtitle;
  final String link;

  Map<String, Object> toJson() => {
    'kind': kind.name, 'text': text, 'subtitle': subtitle, 'link': link,
  };

  factory SiteBlock.fromJson(Map<String, dynamic> json) => SiteBlock(
    kind: SiteBlockKind.values.byName(json['kind'] as String),
    text: json['text'] as String,
    subtitle: json['subtitle'] as String? ?? '',
    link: json['link'] as String? ?? '',
  );
}

class NoCodeSite {
  const NoCodeSite({
    required this.name, required this.heading,
    this.description = '', this.accent = '#876BFF',
    this.background = '#0B0A11', this.blocks = const [],
  });
  final String name;
  final String heading;
  final String description;
  final String accent;
  final String background;
  final List<SiteBlock> blocks;

  Map<String, Object> toJson() => {
    'format': 'unthinkable-web-nocode-local-v1',
    'name': name, 'heading': heading, 'description': description,
    'accent': accent, 'background': background,
    'blocks': blocks.map((b) => b.toJson()).toList(),
  };

  factory NoCodeSite.fromJson(Map<String, dynamic> raw) {
    if (raw['format'] != 'unthinkable-web-nocode-local-v1') {
      throw const FormatException('Nieobsługiwany format strony.');
    }
    final items = raw['blocks'];
    if (items is! List || items.length > 60) throw const FormatException('Nieprawidłowe bloki.');
    return NoCodeSite(
      name: raw['name'] as String, heading: raw['heading'] as String,
      description: raw['description'] as String? ?? '',
      accent: raw['accent'] as String? ?? '#876BFF',
      background: raw['background'] as String? ?? '#0B0A11',
      blocks: items.map((b) => SiteBlock.fromJson(Map<String, dynamic>.from(b as Map))).toList(),
    );
  }

  static final _color = RegExp(r'^#[0-9a-fA-F]{6}$');

  void validate() {
    if (name.trim().isEmpty || name.length > 120 ||
        heading.trim().isEmpty || heading.length > 1200 ||
        description.length > 320 || blocks.length > 60 ||
        !_color.hasMatch(accent) || !_color.hasMatch(background)) {
      throw const FormatException('Nieprawidłowe parametry projektu.');
    }
    for (final block in blocks) {
      if (block.text.trim().isEmpty || block.text.length > 1200 ||
          block.subtitle.length > 500) {
        throw const FormatException('Nieprawidłowy tekst elementu.');
      }
      if (block.kind == SiteBlockKind.button) {
        final link = block.link;
        final uri = Uri.tryParse(link);
        final local = link.startsWith('/') && !link.startsWith('//') &&
            !link.startsWith('/\\');
        final https = uri != null && uri.scheme == 'https' &&
            uri.hasAuthority && uri.userInfo.isEmpty;
        if ((!local && !https) || link.contains(RegExp(r"""["'<>\r\n]"""))) {
          throw const FormatException('Przycisk wymaga linku HTTPS lub ścieżki.');
        }
      } else if (block.link.isNotEmpty) {
        throw const FormatException('Link można podać wyłącznie dla przycisku.');
      }
    }
  }

  String toHtml() {
    validate();
    const txt = HtmlEscape(HtmlEscapeMode.element);
    const attr = HtmlEscape(HtmlEscapeMode.attribute);
    final blocksHtml = blocks.map((block) {
      final content = txt.convert(block.text);
      switch (block.kind) {
        case SiteBlockKind.paragraph:
          return '<p>' + content + '</p>';
        case SiteBlockKind.feature:
          return '<article class="feature"><h2>' + content +
              '</h2><p>' + txt.convert(block.subtitle) + '</p></article>';
        case SiteBlockKind.button:
          return '<a class="button" href="' + attr.convert(block.link) +
              '" rel="noopener noreferrer">' + content + '</a>';
      }
    }).join('\n');
    return '''<!doctype html>
<html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="''' + attr.convert(description) + '''">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri 'none'; object-src 'none'; form-action 'none'; style-src 'unsafe-inline';">
<title>''' + txt.convert(name) + '''</title>
<style>
:root{color-scheme:dark;--bg:''' + background + ''';--accent:''' + accent + '''}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:#fff;font:17px/1.6 system-ui,sans-serif}
main{max-width:950px;margin:auto;padding:clamp(30px,8vw,90px) 24px}
h1{font-size:clamp(34px,8vw,76px);line-height:1.1;letter-spacing:-.04em}
p{color:#c8c5ce}.feature{border:1px solid #ffffff25;padding:22px;margin:16px 0;border-radius:18px}
.button{display:inline-block;margin:16px 0;padding:14px 24px;background:var(--accent);color:#111;text-decoration:none;border-radius:12px;font-weight:700}
footer{text-align:center;border-top:1px solid #ffffff20;padding:32px;color:#aaa}
</style></head><body><main><header><strong>''' + txt.convert(name) +
'''</strong></header><h1>''' + txt.convert(heading) +
'''</h1><p>''' + txt.convert(description) + '''</p>
''' + blocksHtml +
'''</main><footer>Unthinkable AI • NoCode Creator</footer></body></html>''';
  }
}

class WrapperOperation {
  const WrapperOperation({
    required this.name, required this.method,
    required this.path, required this.summary,
  });
  final String name, method, path, summary;
}

Map<String, Object> buildOpenApi(String title, List<WrapperOperation> ops) {
  if (title.trim().isEmpty || title.length > 120 || ops.isEmpty || ops.length > 60) {
    throw const FormatException('Podaj nazwę API i co najmniej jedną operację.');
  }
  final paths = <String, Map<String, Object>>{};
  final ids = <String>{};
  final routes = <String>{};
  final pattern = RegExp(r'^/(?:[a-zA-Z0-9_-]+/?){1,15}$');
  for (final op in ops) {
    if (!RegExp(r'^[a-z][a-z0-9_]{1,69}$').hasMatch(op.name) ||
        !pattern.hasMatch(op.path) || op.path.contains('//') ||
        !const {'GET', 'POST', 'PUT', 'PATCH', 'DELETE'}.contains(op.method) ||
        op.summary.trim().isEmpty || op.summary.length > 240 ||
        !ids.add(op.name) || !routes.add(op.method + ' ' + op.path)) {
      throw const FormatException('Powielone lub nieprawidłowe operacje API.');
    }
    paths.putIfAbsent(op.path, () => {})[op.method.toLowerCase()] = {
      'operationId': op.name,
      'summary': op.summary,
      'responses': {'200': {'description': 'Backend do zaimplementowania'}},
    };
  }
  return {
    'openapi': '3.1.0',
    'info': {
      'title': title.trim(), 'version': '1.0.0',
      'description': 'Kontrakt NoCode — backend jeszcze nie jest połączony',
    },
    'paths': paths,
    'x-unthinkable-capabilities': {
      'contract_generated': true, 'backend_connected': false,
      'proxy_started': false,
    },
  };
}
