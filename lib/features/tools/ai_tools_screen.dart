import 'package:flutter/material.dart';

import '../diffusion/model_library_screen.dart';
import '../video/storyboard.dart';
import 'ai_tools_catalog.dart';

/// First-party interface inspired by the supplied navigation screenshots.
/// Real execution depends on individual native model/provider integrations.
class AiToolsScreen extends StatefulWidget {
  const AiToolsScreen({super.key});

  @override
  State<AiToolsScreen> createState() => _AiToolsScreenState();
}

class _AiToolsScreenState extends State<AiToolsScreen> {
  StudioCategory _category = StudioCategory.all;

  String _categoryLabel(StudioCategory value) => switch (value) {
    StudioCategory.all => 'Wszystko',
    StudioCategory.video => 'Wideo',
    StudioCategory.image => 'Obrazy',
    StudioCategory.audio => 'Audio',
  };

  IconData _categoryIcon(StudioCategory value) => switch (value) {
    StudioCategory.all => Icons.grid_view_outlined,
    StudioCategory.video => Icons.movie_outlined,
    StudioCategory.image => Icons.image_outlined,
    StudioCategory.audio => Icons.music_note_outlined,
  };

  void _open(AiStudioTool tool) {
    if (tool.launch == StudioLaunch.filmStudio) {
      Navigator.of(context).push(
        MaterialPageRoute<void>(builder: (_) => const FilmStudioScreen()),
      );
      return;
    }
    if (tool.launch == StudioLaunch.modelLibrary) {
      Navigator.of(context).push(
        MaterialPageRoute<void>(builder: (_) => const ModelLibraryScreen()),
      );
      return;
    }
    showDialog<void>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: Text(tool.title),
        content: Text(
          tool.description + '\n\n'
          'Ten silnik nie został jeszcze wdrożony ani uruchomiony. '
          'Karta jest przygotowanym miejscem dla modułu i grafiki właściciela.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialog),
            child: const Text('Zamknij'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    const purple = Color(0xFF8066FF);
    final displayed = toolsForCategory(_category);
    return Scaffold(
      appBar: AppBar(title: const Text('Narzędzia AI')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Container(
          padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 18),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF1B1038), Color(0xFF09090A)],
              begin: Alignment.topLeft, end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Narzędzia AI', style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 12),
            const Text('Pracuj z obrazem, wideo i dźwiękiem. '
                'Docelowe grafiki modułów zostaną dodane z Twoich materiałów.'),
          ]),
        ),
        const SizedBox(height: 22),
        if (_category == StudioCategory.all) ...[
          Text('Popularne', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 10),
          for (final tool in aiStudioTools.where((t) => t.featured))
            _ToolCard(tool: tool, large: true, onOpen: () => _open(tool)),
          const SizedBox(height: 16),
        ],
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(children: [
            for (final category in StudioCategory.values)
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(
                  key: Key('studio_tab_' + category.name),
                  avatar: Icon(_categoryIcon(category), size: 18),
                  label: Text(_categoryLabel(category)),
                  selected: category == _category,
                  onSelected: (_) => setState(() => _category = category),
                  selectedColor: purple.withValues(alpha: 0.25),
                ),
              ),
          ]),
        ),
        const SizedBox(height: 12),
        for (final tool in displayed)
          _ToolCard(tool: tool, large: false, onOpen: () => _open(tool)),
        const SizedBox(height: 30),
      ]),
    );
  }
}

class _ToolCard extends StatelessWidget {
  const _ToolCard({required this.tool, required this.large, required this.onOpen});
  final AiStudioTool tool;
  final bool large;
  final VoidCallback onOpen;

  @override
  Widget build(BuildContext context) {
    final prototype = tool.launch == StudioLaunch.requiresEngine;
    return Card(
      margin: const EdgeInsets.only(bottom: 11),
      shape: RoundedRectangleBorder(
        side: const BorderSide(color: Color(0xFF2D2938)),
        borderRadius: BorderRadius.circular(19),
      ),
      child: InkWell(
        key: Key('ai_tool_' + tool.id),
        borderRadius: BorderRadius.circular(19),
        onTap: onOpen,
        child: Padding(
          padding: EdgeInsets.all(large ? 18 : 15),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (large) ...[
                Icon(tool.icon, size: 32, color: const Color(0xFFAA99FF)),
                const SizedBox(height: 32),
              ],
              Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                if (!large) ...[
                  Icon(tool.icon, size: 26, color: const Color(0xFFAA99FF)),
                  const SizedBox(width: 14),
                ],
                Expanded(child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(tool.title,
                      style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                    const SizedBox(height: 5),
                    Text(tool.description,
                      style: const TextStyle(color: Color(0xFFBAB6C1))),
                    const SizedBox(height: 6),
                    Text(
                      prototype ? 'Silnik do podłączenia' :
                        tool.launch == StudioLaunch.filmStudio
                          ? 'Dostępne planowanie scen' : 'Dostępna biblioteka modeli',
                      style: const TextStyle(
                        color: Color(0xFFC5B4FF), fontSize: 12),
                    ),
                  ],
                )),
                const Icon(Icons.chevron_right_outlined),
              ]),
            ],
          ),
        ),
      ),
    );
  }
}
