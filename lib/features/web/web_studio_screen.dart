import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'website_creator_screen.dart';
import 'website_project.dart';
import 'web_studio_api.dart';

/// Website Studio — functional frontend for Scraper, Wrapper and NoCode Builder.
class WebStudioScreen extends StatefulWidget {
  const WebStudioScreen({super.key, this.client});
  final WebStudioApiClient? client;
  @override
  State<WebStudioScreen> createState() => _WebStudioScreenState();
}

class _WebStudioScreenState extends State<WebStudioScreen> {
  final _baseUrl = TextEditingController();
  final _apiKey = TextEditingController();
  final _sourceUrl = TextEditingController();
  late final WebStudioApiClient _api;
  Map<String, dynamic>? _snapshot;
  Map<String, dynamic>? _wrapper;
  bool _busy = false;
  bool _approved = false;
  String? _message;

  @override
  void initState() {
    super.initState();
    _api = widget.client ?? WebStudioApiClient();
  }

  Future<void> _scan() async {
    if (_busy) return;
    setState(() {
      _busy = true; _message = null; _snapshot = null; _wrapper = null;
    });
    try {
      final result = await _api.scan(
        baseUrl: _baseUrl.text, apiKey: _apiKey.text,
        url: _sourceUrl.text, confirmed: _approved,
      );
      if (mounted) setState(() => _snapshot = result);
    } on Object catch (error) {
      if (mounted) setState(() => _message = error is WebStudioApiException
          ? error.message : 'Odrzucono adres, uprawnienia lub parametry.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _wrap() async {
    if (_busy || _snapshot == null) return;
    setState(() { _busy = true; _message = null; });
    try {
      final result = await _api.wrap(
        baseUrl: _baseUrl.text, apiKey: _apiKey.text, snapshot: _snapshot!,
      );
      if (mounted) setState(() => _wrapper = result);
    } on Object catch (error) {
      if (mounted) setState(() => _message = error is WebStudioApiException
          ? error.message : 'Nie udało się utworzyć wrappera.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _importToNoCode() async {
    if (_busy || _wrapper == null) return;
    setState(() { _busy = true; _message = null; });
    try {
      final site = await _api.importToEditor(
        baseUrl: _baseUrl.text, apiKey: _apiKey.text, wrapper: _wrapper!,
      );
      if (mounted) Navigator.of(context).push(MaterialPageRoute<void>(
        builder: (_) => WebsiteCreatorScreen(initial: site,
          apiBaseUrl: _baseUrl.text, apiKey: _apiKey.text),
      ));
    } on Object catch (error) {
      if (mounted) setState(() => _message = error is WebStudioApiException
          ? error.message : 'Niepoprawny projekt źródłowy.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _copyWrapper() async {
    if (_wrapper == null) return;
    await Clipboard.setData(ClipboardData(
      text: const JsonEncoder.withIndent('  ').convert(_wrapper)));
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Wrapper JSON skopiowany.')),
    );
  }

  @override
  void dispose() {
    _baseUrl.dispose();
    _apiKey.clear();
    _apiKey.dispose();
    _sourceUrl.dispose();
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => DefaultTabController(
    length: 3,
    child: Scaffold(
      appBar: AppBar(title: const Text('Website Studio')),
      body: SafeArea(child: Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
          child: Column(children: [
            const Text('Web Scraper, API Wrapper i NoCode Website Creator. '
                'Dane dostępowe wyłącznie w pamięci bieżącej sesji.'),
            const SizedBox(height: 10),
            TextField(key: const Key('web_api_endpoint'),
              controller: _baseUrl, keyboardType: TextInputType.url,
              decoration: const InputDecoration(
                labelText: 'Własny serwer HTTPS', border: OutlineInputBorder())),
            const SizedBox(height: 8),
            TextField(key: const Key('web_api_key'),
              controller: _apiKey, obscureText: true, autocorrect: false,
              enableSuggestions: false,
              decoration: const InputDecoration(
                labelText: 'Klucz API backendu', border: OutlineInputBorder())),
            if (_message != null)
              Text(_message!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
          ]),
        ),
        const TabBar(tabs: [
          Tab(text: 'Scraper', icon: Icon(Icons.travel_explore)),
          Tab(text: 'Wrapper', icon: Icon(Icons.api)),
          Tab(text: 'NoCode', icon: Icon(Icons.web)),
        ]),
        Expanded(child: TabBarView(children: [
          ListView(padding: const EdgeInsets.all(16), children: [
            Text('Autoryzowany skaner strony', style: Theme.of(context).textTheme.titleLarge),
            const Text('Serwer pobiera do 3 podstron z listy zatwierdzonych domen. '
              'Nie pobiera haseł, prywatnej bazy danych ani backendu.'),
            const SizedBox(height: 12),
            TextField(key: const Key('web_source_url'), controller: _sourceUrl,
              keyboardType: TextInputType.url,
              decoration: const InputDecoration(labelText: 'URL witryny HTTPS',
                border: OutlineInputBorder())),
            CheckboxListTile(
              key: const Key('web_confirm_ownership'),
              contentPadding: EdgeInsets.zero,
              title: const Text('Mam prawo analizować tę witrynę'),
              subtitle: const Text('Serwer dodatkowo wymaga domeny na allowliście.'),
              value: _approved,
              onChanged: (v) => setState(() => _approved = v ?? false),
            ),
            FilledButton.icon(
              key: const Key('web_scan_button'),
              onPressed: _busy ? null : _scan,
              icon: const Icon(Icons.search),
              label: const Text('Zbadaj witrynę'),
            ),
            if (_busy) const LinearProgressIndicator(),
            if (_snapshot != null) ...[
              const SizedBox(height: 16),
              Text('Przeanalizowane strony: ' +
                (_snapshot!['pages_scanned'] ?? 0).toString()),
              for (final page in _snapshot!['pages'] as List)
                if (page is Map)
                  Card(child: ListTile(
                    title: Text((page['title'] ?? 'Bez tytułu').toString()),
                    subtitle: Text((page['url'] ?? '').toString()),
                  )),
            ],
          ]),
          ListView(padding: const EdgeInsets.all(16), children: [
            Text('API Wrapper Builder', style: Theme.of(context).textTheme.titleLarge),
            const Text('Przekształca wyniki skanowania w wersjonowany '
              'model danych JSON. Nie jest proxy logowania do cudzej strony.'),
            const SizedBox(height: 12),
            FilledButton.icon(
              key: const Key('web_wrapper_button'),
              onPressed: _snapshot == null || _busy ? null : _wrap,
              icon: const Icon(Icons.account_tree_outlined),
              label: const Text('Utwórz wrapper'),
            ),
            if (_wrapper == null)
              const Padding(padding: EdgeInsets.symmetric(vertical: 16),
                child: Text('Najpierw użyj zakładki Scraper.')),
            if (_wrapper != null) ...[
              const SizedBox(height: 12),
              Text('Strony: ' + (_wrapper!['pages'] as List).length.toString()),
              FilledButton.icon(
                key: const Key('web_import_nocode'),
                onPressed: _busy ? null : _importToNoCode,
                icon: const Icon(Icons.web_outlined),
                label: const Text('Otwórz jako projekt NoCode'),
              ),
              OutlinedButton(
                onPressed: _copyWrapper,
                child: const Text('Kopiuj wrapper JSON'),
              ),
              SelectableText(const JsonEncoder.withIndent('  ').convert(_wrapper)),
            ],
          ]),
          ListView(padding: const EdgeInsets.all(16), children: [
            Text('NoCode Website Creator',
              style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 10),
            const Text('Twórz podstrony, sekcje Hero, tekst, zalety, CTA '
              'i kontakt. Zmieniaj motyw, układ, kopiuj HTML oraz eksportuj '
              'wielostronicową witrynę do ZIP przez swój backend.'),
            const SizedBox(height: 18),
            FilledButton.icon(
              key: const Key('web_open_nocode'),
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(builder: (_) => WebsiteCreatorScreen(
                  apiBaseUrl: _baseUrl.text, apiKey: _apiKey.text))),
              icon: const Icon(Icons.draw_outlined),
              label: const Text('Uruchom kreator NoCode'),
            ),
            const SizedBox(height: 18),
            const Text('Na docelowe grafiki przygotowano miejsca w projekcie UI. '
              'Można podłączyć je bez zmiany kontraktów backendowych.'),
          ]),
        ])),
      ])),
    ),
  );
}
