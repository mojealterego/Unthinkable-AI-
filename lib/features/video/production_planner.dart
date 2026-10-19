import 'package:flutter/material.dart';
import 'production_api.dart';

/// User-triggered planner; does not invoke image/video rendering.
class ProductionPlannerScreen extends StatefulWidget {
  const ProductionPlannerScreen({required this.project, this.client, super.key});
  final Map<String, Object> project;
  final ProductionApiClient? client;

  @override
  State<ProductionPlannerScreen> createState() => _ProductionPlannerScreenState();
}

class _ProductionPlannerScreenState extends State<ProductionPlannerScreen> {
  late final ProductionApiClient _api;
  final _url = TextEditingController();
  final _key = TextEditingController();
  Map<String, dynamic>? _plan;
  String? _error;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _api = widget.client ?? ProductionApiClient();
  }

  Future<void> _run() async {
    if (_loading) return;
    setState(() {
      _loading = true;
      _error = null;
      _plan = null;
    });
    try {
      final result = await _api.planFilm(
        baseUrl: _url.text, apiKey: _key.text, project: widget.project,
      );
      if (mounted) setState(() => _plan = result);
    } on FormatException {
      if (mounted) setState(() => _error = 'Sprawdź adres serwera, klucz i sceny.');
    } on ProductionApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } on Object {
      if (mounted) setState(() => _error = 'Błąd połączenia lub odpowiedzi serwera.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _url.dispose();
    _key.clear();
    _key.dispose();
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final result = _plan;
    return Scaffold(
      appBar: AppBar(title: const Text('Koordynacja produkcji')),
      body: SafeArea(child: ListView(padding: const EdgeInsets.all(16), children: [
        const Text('Zaplanuj prawdziwe ujęcia przez własny backend Unthinkable AI. '
            'Dane zostaną przesłane dopiero po naciśnięciu przycisku. '
            'Nie powoduje to generowania filmów ani wydatków na modele.'),
        const SizedBox(height: 12),
        Text('Projekt: ' + (widget.project['title'] ?? '').toString() +
            ' • scen: ' + (widget.project['shots'] as List).length.toString()),
        const SizedBox(height: 12),
        TextField(
          key: const Key('production_base_url'),
          controller: _url,
          keyboardType: TextInputType.url,
          decoration: const InputDecoration(
            labelText: 'Serwer HTTPS',
            hintText: 'https://studio.example',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 10),
        TextField(
          key: const Key('production_api_key'),
          controller: _key,
          obscureText: true,
          autocorrect: false,
          enableSuggestions: false,
          decoration: const InputDecoration(
            labelText: 'Klucz API — bez zapisu na dysku',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        FilledButton.icon(
          key: const Key('request_production_plan'),
          onPressed: _loading ? null : _run,
          icon: const Icon(Icons.account_tree_outlined),
          label: Text(_loading ? 'Trwa planowanie…' : 'Wyślij i zaplanuj film'),
        ),
        if (_loading) const LinearProgressIndicator(),
        if (_error != null) ...[
          const SizedBox(height: 8),
          Text(_error!, style: const TextStyle(color: Colors.orangeAccent)),
        ],
        if (result != null) ...[
          const SizedBox(height: 16),
          Text('Plan: ' + result['project_title'].toString(),
              style: Theme.of(context).textTheme.titleLarge),
          Text('Czas: ' + result['duration_seconds'].toString() + ' s'),
          const Text('Status: planowanie. Wideo nie zostało wygenerowane.'),
          const SizedBox(height: 12),
          Text('Sceny i referencje', style: Theme.of(context).textTheme.titleMedium),
          for (final entry in (result['scenes'] as List))
            if (entry is Map)
              ListTile(
                leading: Icon(entry['approved'] == true
                    ? Icons.check_circle_outline : Icons.pending_outlined),
                title: Text(entry['name'].toString()),
                subtitle: Text(
                  entry['start_seconds'].toString() + '–' +
                  entry['end_seconds'].toString() + ' s • aktor: ' +
                  (entry['actor_reference'] ?? '').toString(),
                ),
              ),
          const Divider(),
          Text('Ekipa filmowa (18 ról)', style: Theme.of(context).textTheme.titleMedium),
          for (final role in (result['crew'] as List))
            if (role is Map)
              ListTile(
                dense: true,
                title: Text(role['agent'].toString()),
                subtitle: Text(role['purpose'].toString()),
              ),
          const Text('Plan wymaga niezależnej akceptacji przed produkcją.'),
        ],
      ])),
    );
  }
}
