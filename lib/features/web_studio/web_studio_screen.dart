import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'nocode_engine.dart';
import 'web_studio_api.dart';

class WebStudioScreen extends StatefulWidget {
  const WebStudioScreen({super.key, this.client});
  final WebStudioApi? client;
  @override State<WebStudioScreen> createState() => _WebStudioScreenState();
}

class _WebStudioScreenState extends State<WebStudioScreen> {
  final server = TextEditingController();
  final secret = TextEditingController();
  late final WebStudioApi api;

  @override
  void initState() {
    super.initState();
    api = widget.client ?? WebStudioApi();
  }

  @override
  void dispose() {
    server.dispose();
    secret.clear();
    secret.dispose();
    api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => DefaultTabController(
    length: 3,
    child: Scaffold(
      appBar: AppBar(
        title: const Text('Web Engineering Studio'),
        bottom: const TabBar(tabs: [
          Tab(icon: Icon(Icons.travel_explore), text: 'Scraper'),
          Tab(icon: Icon(Icons.api), text: 'Wrapper'),
          Tab(icon: Icon(Icons.web), text: 'NoCode WWW'),
        ]),
      ),
      body: SafeArea(child: Column(children: [
        ExpansionTile(
          title: const Text('Połączenie z własnym backendem HTTPS'),
          subtitle: const Text('Opcjonalne dla kreatora WWW. Klucz nie jest zapisywany.'),
          childrenPadding: const EdgeInsets.all(12),
          children: [
            TextField(
              key: const Key('web_server_url'),
              controller: server,
              decoration: const InputDecoration(
                labelText: 'Adres serwera HTTPS',
                hintText: 'https://moj-serwer.example',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              key: const Key('web_server_key'),
              controller: secret,
              obscureText: true,
              enableSuggestions: false,
              autocorrect: false,
              decoration: const InputDecoration(
                labelText: 'Klucz API serwera',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        Expanded(child: TabBarView(children: [
          _ScraperPanel(api: api, server: server, secret: secret),
          _WrapperPanel(api: api, server: server, secret: secret),
          const _NoCodePanel(),
        ])),
      ])),
    ),
  );
}

class _ScraperPanel extends StatefulWidget {
  const _ScraperPanel({required this.api, required this.server, required this.secret});
  final WebStudioApi api;
  final TextEditingController server, secret;
  @override State<_ScraperPanel> createState() => _ScraperPanelState();
}

class _ScraperPanelState extends State<_ScraperPanel> {
  final url = TextEditingController();
  final html = TextEditingController();
  Map<String, dynamic>? result;
  String? error;
  bool busy = false;

  Future<void> inspect() async {
    if (busy) return;
    setState(() { busy = true; error = null; result = null; });
    try {
      final value = await widget.api.inspect(
        server: widget.server.text, apiKey: widget.secret.text,
        url: url.text, html: html.text,
      );
      if (mounted) setState(() => result = value);
    } on FormatException catch (exception) {
      if (mounted) setState(() => error = exception.message);
    } on WebStudioException catch (exception) {
      if (mounted) setState(() => error = exception.message);
    } on Object {
      if (mounted) setState(() => error = 'Nie można przeprowadzić analizy strony.');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override void dispose() {
    url.dispose(); html.dispose(); super.dispose();
  }

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(16),
    children: [
      Text('Web Scraper', style: Theme.of(context).textTheme.headlineSmall),
      const Text('Analizuje strukturę stron, do których masz uprawnienia. '
          'Bez wykonywania skryptów i odczytu prywatnego backendu.'),
      const SizedBox(height: 12),
      TextField(
        key: const Key('scraper_url'), controller: url,
        keyboardType: TextInputType.url,
        decoration: const InputDecoration(
          labelText: 'Adres dozwolonej strony HTTPS',
          border: OutlineInputBorder(),
        ),
      ),
      const SizedBox(height: 12),
      TextField(
        key: const Key('scraper_html'), controller: html,
        minLines: 3, maxLines: 6,
        decoration: const InputDecoration(
          labelText: 'Lub wklej HTML do analizy (bez pobierania z sieci)',
          border: OutlineInputBorder(),
        ),
      ),
      const SizedBox(height: 12),
      FilledButton.icon(
        key: const Key('scraper_inspect'),
        onPressed: busy ? null : inspect,
        icon: const Icon(Icons.fact_check_outlined),
        label: Text(busy ? 'Analizuję…' : 'Analizuj strukturę'),
      ),
      if (_status(error) != null) Text(_status(error)!),
      if (result != null) ...[
        const Divider(height: 30),
        Text('Tytuł: ' + (result!['title'] ?? '').toString(),
            style: Theme.of(context).textTheme.titleLarge),
        Text('Formularze: ' + (result!['forms_count'] ?? 0).toString()),
        Text('Nagłówki', style: Theme.of(context).textTheme.titleMedium),
        for (final heading in (result!['headings'] as List? ?? []))
          if (heading is Map) ListTile(
            title: Text((heading['text'] ?? '').toString()),
            subtitle: Text((heading['level'] ?? '').toString()),
          ),
        Text('Linki', style: Theme.of(context).textTheme.titleMedium),
        for (final link in (result!['links'] as List? ?? []).take(20))
          if (link is Map) ListTile(
            title: Text((link['text'] ?? 'Link').toString()),
            subtitle: Text((link['href'] ?? '').toString()),
          ),
        const Text('Raport nie zawiera kluczy dostępu ani ukrytego kodu serwera.'),
      ],
    ],
  );

  String? _status(String? value) => value;
}

class _WrapperPanel extends StatefulWidget {
  const _WrapperPanel({required this.api, required this.server, required this.secret});
  final WebStudioApi api;
  final TextEditingController server, secret;
  @override State<_WrapperPanel> createState() => _WrapperPanelState();
}

class _WrapperPanelState extends State<_WrapperPanel> {
  final title = TextEditingController(text: 'Moje API');
  final opId = TextEditingController(text: 'list_items');
  final opPath = TextEditingController(text: '/items');
  final summary = TextEditingController(text: 'Lista elementów');
  final operations = <WrapperOperation>[];
  String method = 'GET';
  String? error;
  String? document;
  bool busy = false;

  void add() {
    final next = WrapperOperation(
      name: opId.text.trim(), method: method,
      path: opPath.text.trim(), summary: summary.text.trim(),
    );
    try {
      buildOpenApi(title.text, [...operations, next]);
      setState(() { operations.add(next); error = null; document = null; });
    } on FormatException catch (e) {
      setState(() => error = e.message);
    }
  }

  Future<void> export() async {
    try {
      final data = buildOpenApi(title.text, operations);
      final json = const JsonEncoder.withIndent('  ').convert(data);
      await Clipboard.setData(ClipboardData(text: json));
      if (mounted) setState(() { document = json; error = null; });
    } on FormatException catch (e) {
      setState(() => error = e.message);
    }
  }

  Future<void> verify() async {
    if (busy) return;
    setState(() { busy = true; error = null; });
    try {
      final answer = await widget.api.wrapper(
        server: widget.server.text, apiKey: widget.secret.text,
        title: title.text, operations: operations,
      );
      if (mounted) setState(() => document =
        const JsonEncoder.withIndent('  ').convert(answer));
    } on FormatException catch (e) {
      if (mounted) setState(() => error = e.message);
    } on WebStudioException catch (e) {
      if (mounted) setState(() => error = e.message);
    } on Object {
      if (mounted) setState(() => error = 'Serwer nie zweryfikował kontraktu.');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override void dispose() {
    title.dispose(); opId.dispose(); opPath.dispose(); summary.dispose(); super.dispose();
  }

  @override Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(16),
    children: [
      Text('API Wrapper Creator', style: Theme.of(context).textTheme.headlineSmall),
      const Text('Wygeneruj dokumentację OpenAPI bez kodowania. '
          'Nie pobiera prywatnych endpointów ani tokenów cudzej strony.'),
      const SizedBox(height: 12),
      TextField(key: const Key('wrapper_title'), controller: title,
        decoration: const InputDecoration(labelText: 'Nazwa API')),
      TextField(key: const Key('wrapper_operation_id'), controller: opId,
        decoration: const InputDecoration(labelText: 'ID operacji')),
      TextField(key: const Key('wrapper_path'), controller: opPath,
        decoration: const InputDecoration(labelText: 'Ścieżka /endpoint')),
      DropdownButton<String>(
        key: const Key('wrapper_method'), value: method, isExpanded: true,
        items: const ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
          .map((name) => DropdownMenuItem(value: name, child: Text(name))).toList(),
        onChanged: (value) => setState(() => method = value ?? method),
      ),
      TextField(key: const Key('wrapper_summary'), controller: summary,
        decoration: const InputDecoration(labelText: 'Opis operacji')),
      const SizedBox(height: 12),
      OutlinedButton.icon(
        key: const Key('wrapper_add'), onPressed: add,
        icon: const Icon(Icons.add), label: const Text('Dodaj operację'),
      ),
      for (final op in operations)
        ListTile(
          title: Text(op.method + ' ' + op.path),
          subtitle: Text(op.name + ' — ' + op.summary),
          trailing: IconButton(
            tooltip: 'Usuń operację',
            onPressed: () => setState(() { operations.remove(op); document = null; }),
            icon: const Icon(Icons.delete_outline),
          ),
        ),
      FilledButton.icon(
        key: const Key('wrapper_export'), onPressed: export,
        icon: const Icon(Icons.content_copy), label: const Text('Eksport OpenAPI JSON'),
      ),
      TextButton(
        key: const Key('wrapper_backend_verify'),
        onPressed: busy ? null : verify,
        child: Text(busy ? 'Weryfikuję…' : 'Sprawdź kontrakt w backendzie'),
      ),
      if (error != null) Text(error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
      if (document != null) SelectableText(document!, maxLines: 24),
      const SizedBox(height: 12),
      const Text('To jest kontrakt API. Połączenie z rzeczywistym backendem '
          'wymaga osobnego, autoryzowanego adaptera.'),
    ],
  );
}

class _NoCodePanel extends StatefulWidget {
  const _NoCodePanel();
  @override State<_NoCodePanel> createState() => _NoCodePanelState();
}

class _NoCodePanelState extends State<_NoCodePanel> {
  static const storage = 'unthinkable.webstudio.nocode.v1';
  final name = TextEditingController(text: 'Moja strona');
  final heading = TextEditingController(text: 'Witaj na mojej stronie');
  final desc = TextEditingController(text: 'Profesjonalna strona bez kodowania');
  final itemTitle = TextEditingController();
  final itemDescription = TextEditingController();
  final itemLink = TextEditingController(text: '/kontakt');
  final blocks = <SiteBlock>[];
  SiteBlockKind blockType = SiteBlockKind.feature;
  String accent = '#876BFF';
  String background = '#0B0A11';
  String? error;
  bool preview = false;

  @override void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final preferences = await SharedPreferences.getInstance();
      final saved = preferences.getString(storage);
      if (saved != null) {
        final value = NoCodeSite.fromJson(
            jsonDecode(saved) as Map<String, dynamic>);
        value.validate();
        if (mounted) setState(() {
          name.text = value.name;
          heading.text = value.heading;
          desc.text = value.description;
          accent = value.accent;
          background = value.background;
          blocks.addAll(value.blocks);
        });
      }
    } on Object {
      if (mounted) setState(() => error = 'Nie udało się odczytać zapisanej strony.');
    }
  }

  NoCodeSite _design() => NoCodeSite(
    name: name.text.trim(), heading: heading.text.trim(),
    description: desc.text.trim(), accent: accent,
    background: background, blocks: List.of(blocks),
  );

  void addBlock() {
    try {
      final entry = SiteBlock(
        kind: blockType, text: itemTitle.text.trim(),
        subtitle: blockType == SiteBlockKind.feature ? itemDescription.text.trim() : '',
        link: blockType == SiteBlockKind.button ? itemLink.text.trim() : '',
      );
      final updated = _design();
      NoCodeSite(
        name: updated.name, heading: updated.heading,
        description: updated.description, accent: updated.accent,
        background: updated.background, blocks: [...blocks, entry],
      ).validate();
      setState(() { blocks.add(entry); error = null; preview = true; });
      itemTitle.clear();
      itemDescription.clear();
    } on FormatException catch (e) {
      setState(() => error = e.message);
    }
  }

  Future<void> save() async {
    try {
      final site = _design();
      site.validate();
      final preferences = await SharedPreferences.getInstance();
      final done = await preferences.setString(storage, jsonEncode(site.toJson()));
      if (!done) throw const FormatException('Zapis nie został przyjęty.');
      if (mounted) setState(() { preview = true; error = null; });
    } on Object {
      if (mounted) setState(() => error = 'Nie udało się zapisać projektu.');
    }
  }

  Future<void> export() async {
    try {
      final html = _design().toHtml();
      await Clipboard.setData(ClipboardData(text: html));
      if (mounted) setState(() { preview = true; error = null; });
    } on FormatException catch (e) {
      setState(() => error = e.message);
    }
  }

  @override void dispose() {
    name.dispose(); heading.dispose(); desc.dispose();
    itemTitle.dispose(); itemDescription.dispose(); itemLink.dispose();
    super.dispose();
  }

  @override Widget build(BuildContext context) {
    final shade = int.parse(accent.substring(1), radix: 16) | 0xFF000000;
    return ListView(padding: const EdgeInsets.all(16), children: [
      Text('Website Creator NoCode', style: Theme.of(context).textTheme.headlineSmall),
      const Text('Projektuj stronę z bloków. Zapis lokalny i eksport HTML działają bez serwera.'),
      const SizedBox(height: 12),
      TextField(key: const Key('web_site_name'), controller: name,
        decoration: const InputDecoration(labelText: 'Nazwa strony'),
        onChanged: (_) => setState(() {})),
      TextField(key: const Key('web_site_heading'), controller: heading,
        decoration: const InputDecoration(labelText: 'Nagłówek główny'),
        onChanged: (_) => setState(() {})),
      TextField(key: const Key('web_site_description'), controller: desc,
        decoration: const InputDecoration(labelText: 'Podtytuł'),
        onChanged: (_) => setState(() {})),
      const SizedBox(height: 10),
      Wrap(spacing: 7, children: [
        for (final theme in [
          ('Fiolet', '#876BFF'), ('Złoto', '#D4AF37'), ('Błękit', '#67C7FF'),
        ])
          ChoiceChip(
            label: Text(theme.$1), selected: accent == theme.$2,
            onSelected: (_) => setState(() => accent = theme.$2),
          ),
      ]),
      const Divider(height: 26),
      Text('Elementy strony', style: Theme.of(context).textTheme.titleMedium),
      DropdownButton<SiteBlockKind>(
        key: const Key('nocode_block_type'), isExpanded: true, value: blockType,
        items: const [
          DropdownMenuItem(value: SiteBlockKind.feature, child: Text('Karta / zaleta')),
          DropdownMenuItem(value: SiteBlockKind.paragraph, child: Text('Akapit tekstowy')),
          DropdownMenuItem(value: SiteBlockKind.button, child: Text('Przycisk / link')),
        ],
        onChanged: (value) => setState(() => blockType = value ?? blockType),
      ),
      TextField(key: const Key('nocode_block_title'), controller: itemTitle,
        decoration: const InputDecoration(labelText: 'Tekst elementu')),
      if (blockType == SiteBlockKind.feature)
        TextField(controller: itemDescription,
          decoration: const InputDecoration(labelText: 'Opis karty')),
      if (blockType == SiteBlockKind.button)
        TextField(controller: itemLink,
          decoration: const InputDecoration(labelText: 'Docelowy adres HTTPS / ścieżka')),
      OutlinedButton.icon(
        key: const Key('nocode_add_block'), onPressed: addBlock,
        icon: const Icon(Icons.add_box_outlined), label: const Text('Dodaj element'),
      ),
      for (final block in blocks)
        Card(child: ListTile(
          title: Text(block.text), subtitle: Text(block.kind.name + ' • ' + block.subtitle),
          trailing: IconButton(
            tooltip: 'Usuń element',
            onPressed: () => setState(() => blocks.remove(block)),
            icon: const Icon(Icons.delete_outline),
          ),
        )),
      Row(children: [
        Expanded(child: OutlinedButton(
          key: const Key('nocode_save'), onPressed: save,
          child: const Text('Zapisz projekt'),
        )),
        const SizedBox(width: 8),
        Expanded(child: FilledButton(
          key: const Key('nocode_export'), onPressed: export,
          child: const Text('Kopiuj HTML'),
        )),
      ]),
      if (error != null) Text(error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
      const SizedBox(height: 22),
      if (preview || heading.text.isNotEmpty) ...[
        Text('Podgląd mobilny', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        Container(
          key: const Key('nocode_preview'),
          decoration: BoxDecoration(
            color: Color(int.parse(background.substring(1), radix: 16) | 0xFF000000),
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: Colors.white24),
          ),
          padding: const EdgeInsets.all(24),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(name.text, style: const TextStyle(color: Colors.white70)),
            const SizedBox(height: 14),
            Text(heading.text, style: const TextStyle(
              fontWeight: FontWeight.w800, color: Colors.white, fontSize: 27)),
            const SizedBox(height: 9),
            Text(desc.text, style: const TextStyle(color: Colors.white70)),
            for (final b in blocks)
              Padding(
                padding: const EdgeInsets.only(top: 14),
                child: b.kind == SiteBlockKind.button
                    ? Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Color(shade), borderRadius: BorderRadius.circular(12)),
                        child: Text(b.text, style: const TextStyle(color: Colors.black)),
                      )
                    : Card(child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text(b.text, style: const TextStyle(
                              fontWeight: FontWeight.bold, color: Colors.white)),
                          if (b.subtitle.isNotEmpty)
                            Text(b.subtitle, style: const TextStyle(color: Colors.white70)),
                        ]),
                      )),
              ),
          ]),
        ),
      ],
      const SizedBox(height: 18),
      const Text('Eksport tworzy samodzielny plik HTML. Hosting, baza danych '
          'i publikacja w Internecie wymagają dodatkowych integracji.'),
    ]);
  }
}
