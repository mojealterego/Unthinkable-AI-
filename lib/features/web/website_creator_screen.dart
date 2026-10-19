import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'website_project.dart';

/// Functional Android-first NoCode editor. Graphics/theme assets are supplied later.
class WebsiteCreatorScreen extends StatefulWidget {
  const WebsiteCreatorScreen({super.key, this.initial});
  final WebsiteProject? initial;
  @override
  State<WebsiteCreatorScreen> createState() => _WebsiteCreatorScreenState();
}

class _WebsiteCreatorScreenState extends State<WebsiteCreatorScreen> {
  static const storageKey = 'unthinkable.nocode.website.v1';
  late WebsiteProject site;
  final titleController = TextEditingController();
  final taglineController = TextEditingController();
  int selected = 0;
  bool ready = false;

  @override
  void initState() {
    super.initState();
    site = widget.initial ?? WebsiteProject();
    titleController.text = site.name;
    taglineController.text = site.tagline;
    if (widget.initial != null) {
      ready = true;
    } else {
      _load();
    }
  }

  Future<void> _load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(storageKey);
      if (raw != null) {
        site = WebsiteProject.fromJson(
          Map<String, dynamic>.from(jsonDecode(raw) as Map),
        );
        titleController.text = site.name;
        taglineController.text = site.tagline;
      }
    } on Object {
      // Malformed local cache must not prevent editing a new website.
    } finally {
      if (mounted) setState(() => ready = true);
    }
  }

  Future<void> _save() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      if (!await prefs.setString(storageKey, site.exportJson())) {
        throw StateError('Cannot store site');
      }
    } on Object {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Nie zapisano projektu lokalnego.')),
      );
    }
  }

  void _change(VoidCallback callback) {
    setState(callback);
    _save();
  }

  Future<void> _addPage() async {
    if (site.pages.length >= 12) return;
    final next = await showDialog<WebsitePage>(
      context: context, builder: (_) => const _NewPageDialog(),
    );
    if (next == null || !mounted) return;
    if (site.pages.any((p) => p.slug == next.slug)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ten identyfikator strony już istnieje.')),
      );
      return;
    }
    _change(() {
      site.pages.add(next);
      selected = site.pages.length - 1;
    });
  }

  Future<void> _addSection() async {
    final result = await showDialog<WebsiteSection>(
      context: context, builder: (_) => const _SectionDialog(),
    );
    if (result == null || !mounted) return;
    _change(() => site.pages[selected].sections.add(result));
  }

  Future<void> _editSection(WebsiteSection current, int index) async {
    final result = await showDialog<WebsiteSection>(
      context: context, builder: (_) => _SectionDialog(existing: current),
    );
    if (result == null || !mounted) return;
    _change(() => site.pages[selected].sections[index] = result);
  }

  Future<void> _copyHtml() async {
    await Clipboard.setData(ClipboardData(text: site.renderHtml(site.pages[selected])));
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('HTML bieżącej strony skopiowany.')),
    );
  }

  Future<void> _copyJson() async {
    await Clipboard.setData(ClipboardData(text: site.exportJson()));
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Pełny projekt JSON skopiowany.')),
    );
  }

  Future<void> _importJson() async {
    final text = (await Clipboard.getData(Clipboard.kTextPlain))?.text;
    if (text == null || !mounted) return;
    try {
      final parsed = WebsiteProject.fromJson(
        Map<String, dynamic>.from(jsonDecode(text) as Map),
      );
      final approved = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Zastąpić projekt?'),
          content: const Text('Import ze schowka zastąpi istniejące strony i sekcje.'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Anuluj')),
            FilledButton(onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Importuj')),
          ],
        ),
      );
      if (approved != true || !mounted) return;
      titleController.text = parsed.name;
      taglineController.text = parsed.tagline;
      _change(() {
        site = parsed;
        selected = 0;
      });
    } on Object {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Nieprawidłowy projekt w schowku.')),
      );
    }
  }

  @override
  void dispose() {
    titleController.dispose();
    taglineController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!ready) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    final page = site.pages[selected];
    return Scaffold(
      appBar: AppBar(title: const Text('NoCode Website Creator')),
      body: SafeArea(child: ListView(padding: const EdgeInsets.all(16), children: [
        const Text('Buduj strony, dodawaj sekcje i zmieniaj ich układ bez kodowania. '
          'Podgląd jest lokalny; publikacja wymaga osobnego hostingu.'),
        const SizedBox(height: 16),
        TextField(
          key: const Key('nocode_site_name'),
          controller: titleController,
          maxLength: 100,
          decoration: const InputDecoration(labelText: 'Nazwa witryny',
            border: OutlineInputBorder()),
          onChanged: (v) => _change(() => site.name = v),
        ),
        TextField(
          key: const Key('nocode_tagline'),
          controller: taglineController,
          maxLength: 200,
          decoration: const InputDecoration(labelText: 'Opis SEO / tagline',
            border: OutlineInputBorder()),
          onChanged: (v) => _change(() => site.tagline = v),
        ),
        const SizedBox(height: 8),
        Text('Motyw', style: Theme.of(context).textTheme.titleMedium),
        Wrap(spacing: 8, children: [
          for (final theme in ['midnight', 'gold', 'light'])
            ChoiceChip(
              key: Key('theme_' + theme),
              label: Text(switch (theme) {
                'midnight' => 'Nocny fiolet',
                'gold' => 'Czerń i złoto',
                _ => 'Jasny',
              }),
              selected: site.theme == theme,
              onSelected: (_) => _change(() => site.theme = theme),
            ),
        ]),
        const SizedBox(height: 18),
        Row(children: [
          Expanded(child: DropdownButtonFormField<int>(
            key: Key('nocode_page_' + page.slug),
            value: selected,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Edytowana strona',
              border: OutlineInputBorder()),
            items: [
              for (var i = 0; i < site.pages.length; i++)
                DropdownMenuItem(value: i,
                  child: Text(site.pages[i].title + ' (' + site.pages[i].slug + ')')),
            ],
            onChanged: (v) => setState(() => selected = v ?? 0),
          )),
          IconButton(
            key: const Key('nocode_add_page'), tooltip: 'Dodaj podstronę',
            onPressed: site.pages.length >= 12 ? null : _addPage,
            icon: const Icon(Icons.note_add_outlined),
          ),
          IconButton(
            tooltip: 'Usuń podstronę',
            onPressed: page.slug == 'index' ? null : () {
              _change(() {
                site.pages.removeAt(selected);
                selected = 0;
              });
            },
            icon: const Icon(Icons.delete_outline),
          ),
        ]),
        const SizedBox(height: 16),
        Row(children: [
          Expanded(child: Text('Sekcje — ' + page.title,
            style: Theme.of(context).textTheme.titleLarge)),
          FilledButton.icon(
            key: const Key('nocode_add_section'),
            onPressed: page.sections.length >= 35 ? null : _addSection,
            icon: const Icon(Icons.add), label: const Text('Sekcja'),
          ),
        ]),
        const SizedBox(height: 8),
        for (var i = 0; i < page.sections.length; i++)
          Card(key: ValueKey('nocode-section-' + i.toString()), child: ListTile(
            title: Text(page.sections[i].heading),
            subtitle: Text(page.sections[i].type + ' • ' + page.sections[i].body,
              maxLines: 2, overflow: TextOverflow.ellipsis),
            leading: const Icon(Icons.widgets_outlined),
            trailing: Wrap(spacing: 0, children: [
              IconButton(tooltip: 'W górę', icon: const Icon(Icons.arrow_upward),
                onPressed: i == 0 ? null : () => _change(() {
                  final item = page.sections.removeAt(i);
                  page.sections.insert(i - 1, item);
                })),
              IconButton(tooltip: 'Edytuj sekcję', icon: const Icon(Icons.edit_outlined),
                onPressed: () => _editSection(page.sections[i], i)),
              IconButton(tooltip: 'Usuń sekcję', icon: const Icon(Icons.close),
                onPressed: page.sections.length <= 1 ? null :
                  () => _change(() => page.sections.removeAt(i))),
            ]),
          )),
        const SizedBox(height: 18),
        Text('Podgląd mobilny', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: site.theme == 'light'
              ? const Color(0xFFF6F5FA) : const Color(0xFF181524),
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: const Color(0xFF5A5074)),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(site.name, style: TextStyle(
              color: site.theme == 'light' ? Colors.black : Colors.white,
              fontWeight: FontWeight.bold)),
            const Divider(),
            for (final section in page.sections) ...[
              Text(section.heading, style: TextStyle(
                fontSize: section.type == 'hero' ? 25 : 19,
                fontWeight: FontWeight.w700,
                color: site.theme == 'light' ? Colors.black : Colors.white,
              )),
              Text(section.body, style: TextStyle(
                color: site.theme == 'light'
                  ? const Color(0xFF303039) : const Color(0xFFD3CCDF))),
              if (section.type == 'features')
                for (final feature in section.items)
                  Text('• ' + feature, style: TextStyle(
                    color: site.theme == 'light' ? Colors.black : Colors.white)),
              const SizedBox(height: 18),
            ],
          ]),
        ),
        const SizedBox(height: 16),
        Wrap(spacing: 8, runSpacing: 8, children: [
          FilledButton.icon(
            key: const Key('nocode_export_html'),
            onPressed: _copyHtml,
            icon: const Icon(Icons.code), label: const Text('Kopiuj HTML'),
          ),
          OutlinedButton(
            key: const Key('nocode_export_json'),
            onPressed: _copyJson, child: const Text('Eksport JSON'),
          ),
          OutlinedButton(
            key: const Key('nocode_import_json'),
            onPressed: _importJson, child: const Text('Import JSON'),
          ),
        ]),
        const SizedBox(height: 10),
        const Text('Wielostronicowy ZIP jest dostępny w backendowym eksporcie. '
          'Sama aplikacja nie publikuje witryny ani nie kopiuje cudzej bazy danych.'),
        const SizedBox(height: 30),
      ])),
    );
  }
}

class _NewPageDialog extends StatefulWidget {
  const _NewPageDialog();
  @override
  State<_NewPageDialog> createState() => _NewPageDialogState();
}

class _NewPageDialogState extends State<_NewPageDialog> {
  final title = TextEditingController();
  final slug = TextEditingController();
  String? error;

  @override
  void dispose() {
    title.dispose();
    slug.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Nowa podstrona'),
    content: Column(mainAxisSize: MainAxisSize.min, children: [
      TextField(controller: title, maxLength: 120,
        decoration: const InputDecoration(labelText: 'Tytuł')),
      TextField(controller: slug, maxLength: 48,
        decoration: const InputDecoration(labelText: 'Slug, np. kontakt')),
      if (error != null) Text(error!),
    ]),
    actions: [
      TextButton(onPressed: () => Navigator.pop(context),
        child: const Text('Anuluj')),
      FilledButton(onPressed: () {
        if (title.text.trim().isEmpty ||
          !RegExp(r'^[a-z][a-z0-9-]{0,47}$').hasMatch(slug.text) ||
          slug.text == 'index') {
          setState(() => error = 'Wprowadź nazwę i unikalny slug (małe litery).');
          return;
        }
        Navigator.pop(context, WebsitePage(slug: slug.text, title: title.text.trim()));
      }, child: const Text('Dodaj')),
    ],
  );
}

class _SectionDialog extends StatefulWidget {
  const _SectionDialog({this.existing});
  final WebsiteSection? existing;

  @override
  State<_SectionDialog> createState() => _SectionDialogState();
}

class _SectionDialogState extends State<_SectionDialog> {
  late String type;
  late final TextEditingController heading;
  late final TextEditingController body;
  late final TextEditingController items;
  late final TextEditingController buttonLabel;
  late final TextEditingController buttonUrl;
  String? error;

  @override
  void initState() {
    super.initState();
    type = widget.existing?.type ?? 'text';
    heading = TextEditingController(text: widget.existing?.heading ?? '');
    body = TextEditingController(text: widget.existing?.body ?? '');
    items = TextEditingController(text: widget.existing?.items.join('\n') ?? '');
    buttonLabel = TextEditingController(text: widget.existing?.buttonLabel ?? '');
    buttonUrl = TextEditingController(text: widget.existing?.buttonUrl ?? '');
  }

  @override
  void dispose() {
    heading.dispose();
    body.dispose();
    items.dispose();
    buttonLabel.dispose();
    buttonUrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Edytor sekcji NoCode'),
    content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
      DropdownButtonFormField<String>(
        value: type,
        decoration: const InputDecoration(labelText: 'Komponent'),
        items: [
          for (final kind in ['hero','text','features','cta','contact'])
            DropdownMenuItem(value: kind, child: Text(kind)),
        ],
        onChanged: (v) => setState(() => type = v ?? 'text'),
      ),
      TextField(key: const Key('nocode_section_heading'),
        controller: heading, maxLength: 150,
        decoration: const InputDecoration(labelText: 'Nagłówek')),
      TextField(controller: body, minLines: 2, maxLines: 5, maxLength: 3500,
        decoration: const InputDecoration(labelText: 'Treść')),
      if (type == 'features')
        TextField(controller: items, maxLines: 4,
          decoration: const InputDecoration(labelText: 'Elementy (jeden na linię)')),
      TextField(controller: buttonLabel,
        decoration: const InputDecoration(labelText: 'Przycisk: napis (opcjonalne)')),
      TextField(controller: buttonUrl,
        decoration: const InputDecoration(labelText: 'Przycisk: HTTPS / mailto / ścieżka')),
      if (error != null) Text(error!, style: const TextStyle(color: Colors.orange)),
    ])),
    actions: [
      TextButton(onPressed: () => Navigator.pop(context), child: const Text('Anuluj')),
      FilledButton(key: const Key('nocode_save_section'), onPressed: () {
        if (heading.text.trim().isEmpty || !WebsiteProject.safeLink(buttonUrl.text)) {
          setState(() => error = 'Nagłówek i bezpieczny adres URL są wymagane.');
          return;
        }
        final all = items.text.split('\n').map((x) => x.trim())
          .where((x) => x.isNotEmpty).take(12).toList();
        Navigator.pop(context, WebsiteSection(type: type, heading: heading.text.trim(),
          body: body.text, items: all, buttonLabel: buttonLabel.text,
          buttonUrl: buttonUrl.text));
      }, child: const Text('Zapisz sekcję')),
    ],
  );
}
