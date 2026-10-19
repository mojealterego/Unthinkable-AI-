import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'vanity_engine.dart';

/// UI assets are intentionally owner-supplied. This is not a PSTN dialer.
class VirtualNumberScreen extends StatefulWidget {
  const VirtualNumberScreen({super.key});
  @override
  State<VirtualNumberScreen> createState() => _VirtualNumberScreenState();
}

class _VirtualNumberScreenState extends State<VirtualNumberScreen> {
  static const _key = 'unthinkable.onnet_aliases.v1';
  final _prefix = TextEditingController();
  final _engine = const VanityEngine();
  int _length = 9;
  VanityStyle _style = VanityStyle.repeated;
  List<VanityCandidate> _candidates = [];
  List<String> _saved = [];
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    if (mounted) setState(() => _saved = prefs.getStringList(_key) ?? []);
  }

  void _generate() {
    try {
      final proposals = _engine.generate(
        prefix: _prefix.text.trim(), length: _length, style: _style,
      );
      setState(() { _candidates = proposals; _error = null; });
    } on FormatException catch (e) {
      setState(() { _candidates = []; _error = e.message; });
    }
  }

  Future<void> _save(VanityCandidate value) async {
    if (_saved.contains(value.identifier)) return;
    final updated = [value.identifier, ..._saved].take(50).toList();
    try {
      final prefs = await SharedPreferences.getInstance();
      if (!await prefs.setStringList(_key, updated)) throw StateError('Storage error');
      if (mounted) setState(() => _saved = updated);
    } on Object {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Błąd zapisu aliasu.')),
      );
    }
  }

  Future<void> _remove(String alias) async {
    final updated = _saved.where((element) => element != alias).toList();
    try {
      final prefs = await SharedPreferences.getInstance();
      if (!await prefs.setStringList(_key, updated)) throw StateError('Storage error');
      if (mounted) setState(() => _saved = updated);
    } on Object {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Błąd usuwania aliasu.')),
      );
    }
  }

  Future<void> _copy(String alias) async {
    await Clipboard.setData(ClipboardData(text: alias));
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Skopiowano wewnętrzny identyfikator.')),
    );
  }

  @override
  void dispose() {
    _prefix.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const accent = Color(0xFF9B85FF);
    return Scaffold(
      appBar: AppBar(title: const Text('Virtual Number')),
      body: SafeArea(child: ListView(padding: const EdgeInsets.all(16), children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF251745), Color(0xFF0B0A10)],
              begin: Alignment.topLeft, end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(22),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Icon(Icons.phone_in_talk_outlined, size: 36, color: accent),
            const SizedBox(height: 12),
            Text('All Virtual Phone', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            const Text('Generator aliasów złotych, platynowych i losowych. '
              'Miejsce na grafikę przygotowaną przez właściciela.'),
            const SizedBox(height: 12),
            const Text('TRYB WEWNĘTRZNY — NIE JEST TO AKTYWNY NUMER',
              style: TextStyle(color: Color(0xFFE2BF79), fontWeight: FontWeight.w600)),
          ]),
        ),
        const SizedBox(height: 20),
        Text('Wybierz własny wzór', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 12),
        TextField(
          key: const Key('vanity_prefix'),
          controller: _prefix,
          keyboardType: TextInputType.number,
          maxLength: 15,
          decoration: const InputDecoration(
            labelText: 'Dowolny prefiks',
            hintText: 'Np. 111, 000, 798 lub pusty',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 8),
        Text('Długość aliasu: ' + _length.toString() + ' cyfr'),
        Slider(
          key: const Key('vanity_length'), value: _length.toDouble(),
          min: 4, max: 18, divisions: 14, label: _length.toString(),
          onChanged: (value) => setState(() => _length = value.round()),
        ),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(children: [
            for (final style in VanityStyle.values)
              Padding(
                padding: const EdgeInsets.only(right: 6),
                child: ChoiceChip(
                  label: Text(switch (style) {
                    VanityStyle.repeated => 'Powtarzane',
                    VanityStyle.pairs => 'Pary',
                    VanityStyle.sequence => 'Sekwencja',
                    VanityStyle.random => 'Losowe',
                  }),
                  selected: _style == style,
                  onSelected: (_) => setState(() => _style = style),
                ),
              ),
          ]),
        ),
        const SizedBox(height: 12),
        FilledButton.icon(
          key: const Key('generate_aliases'),
          onPressed: _generate,
          icon: const Icon(Icons.auto_awesome),
          label: const Text('Generuj propozycje'),
        ),
        if (_error != null) ...[
          const SizedBox(height: 8),
          Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
        ],
        if (_candidates.isNotEmpty) ...[
          const SizedBox(height: 20),
          Text('Kandydaci — bez rezerwacji', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          for (final item in _candidates)
            Card(child: ListTile(
              leading: const Icon(Icons.dialpad_outlined, color: accent),
              title: Text(item.identifier,
                style: const TextStyle(fontWeight: FontWeight.w700, letterSpacing: 1.0)),
              subtitle: Text(item.tier + ' • ' + item.score.toString() + ' pkt • on-net'),
              trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                IconButton(
                  tooltip: 'Kopiuj alias',
                  onPressed: () => _copy(item.identifier),
                  icon: const Icon(Icons.copy_outlined),
                ),
                IconButton(
                  tooltip: 'Zapisz alias',
                  onPressed: _saved.contains(item.identifier) ? null : () => _save(item),
                  icon: const Icon(Icons.bookmark_add_outlined),
                ),
              ]),
            )),
        ],
        const SizedBox(height: 22),
        Text('Zapisane wzory', style: Theme.of(context).textTheme.titleLarge),
        if (_saved.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Text('Nie zapisano jeszcze aliasów.'),
          ),
        for (final alias in _saved)
          ListTile(
            title: Text(alias),
            subtitle: const Text('Lokalny wzór, bez rezerwacji operatora'),
            trailing: IconButton(
              tooltip: 'Usuń zapisany alias',
              onPressed: () => _remove(alias),
              icon: const Icon(Icons.delete_outline),
            ),
          ),
        const Divider(height: 32),
        Text('Numer publiczny DID', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 10),
        const Text('Wybrany ciąg cyfr nie jest numerem telefonicznym. '
          'Połączenia, SMS/MMS i maskowanie numeru wymagają realnego przydziału DID '
          'przez operatora, weryfikacji uprawnień i uruchomienia infrastruktury VoIP.'),
        const SizedBox(height: 30),
      ])),
    );
  }
}
