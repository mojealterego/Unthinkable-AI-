import 'production_planner.dart';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// A real, local-only shotlist editor, NOT a video generation or NLE engine.
class FilmShot {
  FilmShot({
    required this.id,
    required this.name,
    required this.durationSeconds,
    this.prompt = '',
    this.actorReference = '',
    this.mediaReference = '',
    this.approved = false,
  });

  final String id;
  String name;
  int durationSeconds;
  String prompt;
  String actorReference;
  String mediaReference;
  bool approved;

  Map<String, Object> toJson() => {
    'id': id,
    'name': name,
    'durationSeconds': durationSeconds,
    'prompt': prompt,
    'actorReference': actorReference,
    'mediaReference': mediaReference,
    'approved': approved,
  };

  factory FilmShot.fromJson(Map<String, dynamic> data) {
    final seconds = data['durationSeconds'];
    if (seconds is! int || seconds < 1 || seconds > 86400) {
      throw const FormatException('Invalid shot duration');
    }
    final id = data['id'];
    final name = data['name'];
    if (id is! String || id.isEmpty || name is! String || name.trim().isEmpty) {
      throw const FormatException('Missing shot ID or name');
    }
    return FilmShot(
      id: id,
      name: name,
      durationSeconds: seconds,
      prompt: (data['prompt'] as String?) ?? '',
      actorReference: (data['actorReference'] as String?) ?? '',
      mediaReference: (data['mediaReference'] as String?) ?? '',
      approved: data['approved'] == true,
    );
  }
}

class FilmProject {
  FilmProject({this.title = 'Nowy projekt filmowy', this.masterPrompt = '', List<FilmShot>? shots})
      : shots = shots ?? [];

  String title;
  String masterPrompt;
  final List<FilmShot> shots;

  int get durationSeconds => shots.fold(0, (sum, shot) => sum + shot.durationSeconds);
  bool get isAtLeast123Minutes => durationSeconds >= 123 * 60;
  int get approvedShots => shots.where((s) => s.approved).length;

  Map<String, Object> toJson() => {
    'format': 'unthinkable-film-shotlist-v1',
    'title': title,
    'masterPrompt': masterPrompt,
    'shots': shots.map((shot) => shot.toJson()).toList(),
  };

  factory FilmProject.fromJson(Map<String, dynamic> data) {
    if (data['format'] != 'unthinkable-film-shotlist-v1') {
      throw const FormatException('Unsupported project format');
    }
    final title = data['title'];
    final items = data['shots'];
    if (title is! String || title.trim().isEmpty || items is! List || items.length > 2000) {
      throw const FormatException('Invalid project metadata');
    }
    final shots = items.map((item) {
      if (item is! Map<String, dynamic>) throw const FormatException('Invalid shot');
      return FilmShot.fromJson(item);
    }).toList();
    final ids = shots.map((e) => e.id).toSet();
    if (ids.length != shots.length) throw const FormatException('Duplicate shot IDs');
    return FilmProject(
      title: title,
      masterPrompt: (data['masterPrompt'] as String?) ?? '',
      shots: shots,
    );
  }
}

String formatFilmDuration(int seconds) {
  final hours = seconds ~/ 3600;
  final minutes = (seconds % 3600) ~/ 60;
  final secs = seconds % 60;
  return '${hours.toString().padLeft(2, '0')}:${minutes.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
}

class FilmStudioScreen extends StatefulWidget {
  const FilmStudioScreen({super.key});

  @override
  State<FilmStudioScreen> createState() => _FilmStudioScreenState();
}

class _FilmStudioScreenState extends State<FilmStudioScreen> {
  static const _storageKey = 'unthinkable.film.shotlist.v1';
  FilmProject _project = FilmProject();
  bool _loaded = false;
  int _idCounter = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString(_storageKey);
      if (saved != null) {
        final parsed = jsonDecode(saved);
        if (parsed is! Map<String, dynamic>) throw const FormatException('Invalid JSON project');
        _project = FilmProject.fromJson(parsed);
      }
    } on Object {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Nie można odczytać projektu. Zachowano bieżącą sesję.')),
        );
      }
    }
    if (mounted) setState(() => _loaded = true);
  }

  Future<void> _save() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_storageKey, jsonEncode(_project.toJson()));
    } on Object {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Nie udało się zapisać projektu na urządzeniu.')),
        );
      }
    }
  }

  Future<void> _editProject() async {
    final updated = await showDialog<FilmProject>(
      context: context,
      builder: (_) => _ProjectEditDialog(project: _project),
    );
    if (updated == null || !mounted) return;
    setState(() => _project = updated);
    await _save();
  }

  Future<void> _editShot([FilmShot? existing]) async {
    final id = existing?.id ?? 'shot-${DateTime.now().microsecondsSinceEpoch}-${_idCounter++}';
    final shot = await showDialog<FilmShot>(
      context: context,
      builder: (_) => _ShotEditDialog(existing: existing, id: id),
    );
    if (shot == null || !mounted) return;
    setState(() {
      if (existing == null) {
        _project.shots.add(shot);
      } else {
        final index = _project.shots.indexWhere((s) => s.id == existing.id);
        if (index >= 0) _project.shots[index] = shot;
      }
    });
    await _save();
  }

  Future<void> _export() async {
    await Clipboard.setData(ClipboardData(text: const JsonEncoder.withIndent('  ').convert(_project.toJson())));
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('JSON projektu skopiowany do schowka.')),
    );
  }

  Future<void> _import() async {
    final data = await Clipboard.getData(Clipboard.kTextPlain);
    if (!mounted) return;
    if (data?.text == null) return;
    try {
      final parsed = jsonDecode(data!.text!);
      if (parsed is! Map<String, dynamic>) throw const FormatException('Invalid JSON');
      final incoming = FilmProject.fromJson(parsed);
      final replace = await showDialog<bool>(context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Text('Zastąpić obecny projekt?'),
          content: Text('Zaimportować projekt „${incoming.title}” ze schowka?'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Anuluj')),
            FilledButton(onPressed: () => Navigator.pop(dialogContext, true), child: const Text('Importuj')),
          ],
        ),
      );
      if (replace != true || !mounted) return;
      setState(() => _project = incoming);
      await _save();
    } on Object {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Schowek nie zawiera zgodnego projektu.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_loaded) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    return Scaffold(
      appBar: AppBar(title: const Text('Studio scen i ujęć')),
      floatingActionButton: FloatingActionButton.extended(
        key: const Key('add_shot'),
        onPressed: () => _editShot(),
        icon: const Icon(Icons.add), label: const Text('Dodaj scenę'),
      ),
      body: Column(children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: Card(child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(_project.title, style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              Text('Całkowity czas: ${formatFilmDuration(_project.durationSeconds)} • Zatwierdzone: ${_project.approvedShots}/${_project.shots.length}'),
              Text(_project.isAtLeast123Minutes
                ? 'Plan przekracza 123 minuty'
                : 'Cel 123 minut: brakuje ${formatFilmDuration(123 * 60 - _project.durationSeconds)}'),
              const SizedBox(height: 6),
              const Text('Prawdziwy edytor planu ujęć. Nie generuje i nie montuje jeszcze wideo.',
                style: TextStyle(fontSize: 12)),
              const SizedBox(height: 8),
              Wrap(spacing: 6, runSpacing: 6, children: [
                OutlinedButton(onPressed: _editProject, child: const Text('Master prompt')),
                FilledButton.icon(
                  key: const Key('open_production_planner'),
                  onPressed: _project.shots.isEmpty ? null : () =>
                    Navigator.of(context).push(MaterialPageRoute<void>(
                      builder: (_) => ProductionPlannerScreen(project: _project.toJson()),
                    )),
                  icon: const Icon(Icons.account_tree_outlined),
                  label: const Text('Plan filmowy AI'),
                ),
                OutlinedButton(onPressed: _export, child: const Text('Eksport JSON')),
                OutlinedButton(onPressed: _import, child: const Text('Import JSON')),
              ]),
            ]),
          )),
        ),
        Expanded(child: _project.shots.isEmpty
          ? const Center(child: Text('Dodaj scenę, aby rozpocząć planowanie filmu.'))
          : ReorderableListView.builder(
              itemCount: _project.shots.length,
              onReorder: (from, to) {
                setState(() {
                  if (from < to) to -= 1;
                  final element = _project.shots.removeAt(from);
                  _project.shots.insert(to, element);
                });
                _save();
              },
              itemBuilder: (context, index) {
                final shot = _project.shots[index];
                return Card(
                  key: ValueKey(shot.id),
                  margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  child: Column(children: [
                    ListTile(
                      leading: CircleAvatar(child: Text('${index + 1}')),
                      title: Text(shot.name),
                      subtitle: Text('${formatFilmDuration(shot.durationSeconds)} • ${shot.actorReference.isEmpty ? "Bez referencji aktora" : shot.actorReference}\n${shot.prompt}', maxLines: 3),
                      isThreeLine: true,
                      trailing: PopupMenuButton<String>(
                        onSelected: (choice) {
                          if (choice == 'edit') _editShot(shot);
                          if (choice == 'delete') {
                            setState(() => _project.shots.removeWhere((x) => x.id == shot.id));
                            _save();
                          }
                        },
                        itemBuilder: (context) => const [
                          PopupMenuItem(value: 'edit', child: Text('Edytuj')),
                          PopupMenuItem(value: 'delete', child: Text('Usuń')),
                        ],
                      ),
                    ),
                    CheckboxListTile(
                      dense: true,
                      value: shot.approved,
                      title: const Text('Scena zatwierdzona'),
                      onChanged: (value) {
                        setState(() => shot.approved = value ?? false);
                        _save();
                      },
                    ),
                  ]),
                );
              },
            ),
        ),
      ]),
    );
  }
}

class _ProjectEditDialog extends StatefulWidget {
  const _ProjectEditDialog({required this.project});
  final FilmProject project;

  @override
  State<_ProjectEditDialog> createState() => _ProjectEditDialogState();
}

class _ProjectEditDialogState extends State<_ProjectEditDialog> {
  late final TextEditingController _title;
  late final TextEditingController _prompt;

  @override
  void initState() {
    super.initState();
    _title = TextEditingController(text: widget.project.title);
    _prompt = TextEditingController(text: widget.project.masterPrompt);
  }

  @override
  void dispose() {
    _title.dispose();
    _prompt.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Projekt filmowy'),
    content: SingleChildScrollView(
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(controller: _title, maxLength: 150,
          decoration: const InputDecoration(labelText: 'Tytuł filmu')),
        TextField(controller: _prompt, minLines: 3, maxLines: 8,
          decoration: const InputDecoration(labelText: 'Master prompt całego filmu')),
      ]),
    ),
    actions: [
      TextButton(onPressed: () => Navigator.pop(context), child: const Text('Anuluj')),
      FilledButton(
        onPressed: () {
          if (_title.text.trim().isEmpty) return;
          Navigator.pop(context, FilmProject(
            title: _title.text.trim(), masterPrompt: _prompt.text,
            shots: widget.project.shots,
          ));
        },
        child: const Text('Zapisz'),
      ),
    ],
  );
}

class _ShotEditDialog extends StatefulWidget {
  const _ShotEditDialog({required this.existing, required this.id});
  final FilmShot? existing;
  final String id;

  @override
  State<_ShotEditDialog> createState() => _ShotEditDialogState();
}

class _ShotEditDialogState extends State<_ShotEditDialog> {
  late final TextEditingController _name;
  late final TextEditingController _seconds;
  late final TextEditingController _prompt;
  late final TextEditingController _actor;
  late final TextEditingController _media;

  @override
  void initState() {
    super.initState();
    final existing = widget.existing;
    _name = TextEditingController(text: existing?.name ?? '');
    _seconds = TextEditingController(text: '${existing?.durationSeconds ?? 30}');
    _prompt = TextEditingController(text: existing?.prompt ?? '');
    _actor = TextEditingController(text: existing?.actorReference ?? '');
    _media = TextEditingController(text: existing?.mediaReference ?? '');
  }

  @override
  void dispose() {
    _name.dispose();
    _seconds.dispose();
    _prompt.dispose();
    _actor.dispose();
    _media.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: Text(widget.existing == null ? 'Dodaj scenę' : 'Edytuj scenę'),
    content: SingleChildScrollView(
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(key: const Key('shot_name'), controller: _name, maxLength: 120,
          decoration: const InputDecoration(labelText: 'Nazwa sceny')),
        TextField(key: const Key('shot_seconds'), controller: _seconds,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'Długość w sekundach (1–86400)')),
        TextField(controller: _actor,
          decoration: const InputDecoration(labelText: 'Referencja aktora / postaci')),
        TextField(controller: _media,
          decoration: const InputDecoration(labelText: 'Referencja materiału (ścieżka/URI)')),
        TextField(controller: _prompt, maxLines: 5,
          decoration: const InputDecoration(labelText: 'Prompt i opis sceny')),
      ]),
    ),
    actions: [
      TextButton(onPressed: () => Navigator.pop(context), child: const Text('Anuluj')),
      FilledButton(
        key: const Key('save_shot'),
        onPressed: () {
          final duration = int.tryParse(_seconds.text);
          if (_name.text.trim().isEmpty || duration == null || duration < 1 || duration > 86400) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Podaj nazwę i prawidłowy czas sceny.')),
            );
            return;
          }
          Navigator.pop(context, FilmShot(
            id: widget.id, name: _name.text.trim(), durationSeconds: duration,
            prompt: _prompt.text, actorReference: _actor.text,
            mediaReference: _media.text, approved: widget.existing?.approved ?? false,
          ));
        },
        child: const Text('Zapisz scenę'),
      ),
    ],
  );
}
