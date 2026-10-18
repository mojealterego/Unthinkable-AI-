import 'features/video/storyboard.dart';
import 'package:flutter/material.dart';

void main() => runApp(const UnthinkableAiApp());

/// These are specification domains, NOT implemented AI engines.
class FeatureDomain {
  const FeatureDomain(this.code, this.title, this.details, this.requirements, this.icon);

  final String code;
  final String title;
  final String details;
  final int requirements;
  final IconData icon;
}

/// Mirror of the 339-entry source register; actual IDs stay in requirements.csv.
const domains = <FeatureDomain>[
  FeatureDomain('FOUND', 'Centrum Unthinkable AI', 'Tożsamość, języki, Santa Muerte, intro', 12, Icons.dashboard_outlined),
  FeatureDomain('MODELS', 'Modele AI', 'GGUF, modele lokalne, Hugging Face i API', 16, Icons.memory_outlined),
  FeatureDomain('REASON', 'Rozumowanie i pamięć', 'Weryfikowalna wiedza, RAG i grafy', 14, Icons.psychology_outlined),
  FeatureDomain('AGENTS', 'Agents Builder', 'Code, NoCode, orkiestracja i roje', 14, Icons.hub_outlined),
  FeatureDomain('EXT', 'Wtyczki i narzędzia', 'Skill Creator, Tool Generator, MCP', 10, Icons.extension_outlined),
  FeatureDomain('DEEP', 'Deep Research', 'Źródła, eksperymenty i badania', 13, Icons.science_outlined),
  FeatureDomain('DGM', 'DGM / RSI', 'Kontrolowana ewolucja i aktualizacje', 12, Icons.autorenew_outlined),
  FeatureDomain('GITHUB', 'Inżynier repozytoriów', 'GitHub, GitLab, audyt i CI', 14, Icons.code_outlined),
  FeatureDomain('IMAGE', 'Studio obrazu', 'Stable Diffusion i modele natywne', 12, Icons.image_outlined),
  FeatureDomain('VIDEO', 'Studio filmowe', 'Wan, Pinokio, ekipa, NLE 123+ min', 22, Icons.movie_creation_outlined),
  FeatureDomain('AUDIO', 'Muzyka i głos', 'Muzyka, teledyski, audioksiążki, voice', 10, Icons.graphic_eq_outlined),
  FeatureDomain('GAME', 'Game Builder', 'Code/NoCode, 2D, 3D, AAA, silniki', 14, Icons.sports_esports_outlined),
  FeatureDomain('APPS', 'App Builder i IDE', 'Aplikacje i narzędzia, Code/NoCode', 12, Icons.developer_mode_outlined),
  FeatureDomain('PUBLISH', 'Wydawnictwo AI', 'Ebooki, komiksy, bajki, roleplay', 10, Icons.menu_book_outlined),
  FeatureDomain('CHAT', 'Komunikator i numeracja', 'Pokoje QR, szyfrowanie, legalne aliasy', 13, Icons.forum_outlined),
  FeatureDomain('BROWSER', 'Dwie przeglądarki', 'Clearnet, Tor, OSINT', 11, Icons.travel_explore_outlined),
  FeatureDomain('ANDROID', 'Opiekun Androida', 'Diagnostyka i uprawnienia urządzenia', 9, Icons.phone_android_outlined),
  FeatureDomain('WEB', 'Narzędzia internetowe', 'WWW, scraper, Workspace, aliasy', 10, Icons.language_outlined),
  FeatureDomain('OWNER', 'Prywatna przestrzeń', 'Vault, SFTP, SMB, Google Drive, sandbox', 10, Icons.lock_outline),
  FeatureDomain('MATH', 'Millenium Problems & Cain', 'Solvery, dowody, zagadka Żuchwy Kaina', 12, Icons.functions_outlined),
  FeatureDomain('MARKET', 'Marketplace', 'Agenci, skille, serwery MCP, produkty', 9, Icons.storefront_outlined),
  FeatureDomain('PAY', 'Subskrypcje i płatności', 'Free, premium, PayPal, BLIK, Revolut', 13, Icons.payments_outlined),
  FeatureDomain('INFRA', 'Infrastruktura', 'Edge, cloud, worker, bezpieczeństwo', 19, Icons.dns_outlined),
  FeatureDomain('FORMAL', 'Matematyka i dowody', 'Modele, algorytmy i benchmarki', 18, Icons.calculate_outlined),
  FeatureDomain('LEGAL', 'Prywatność i zgodność', 'Licencje, zgoda, audyt, prawa', 14, Icons.verified_user_outlined),
  FeatureDomain('OPTION', 'Moduły opcjonalne', 'Dodatki wyłącznie po decyzji właściciela', 8, Icons.tune_outlined),
  FeatureDomain('REUSE', 'Analiza istniejących projektów', 'Audyt i wykorzystanie repozytoriów', 8, Icons.inventory_2_outlined),
];

class UnthinkableAiApp extends StatelessWidget {
  const UnthinkableAiApp({super.key});

  @override
  Widget build(BuildContext context) {
    const gold = Color(0xFFD4AF37);
    return MaterialApp(
      title: 'Unthinkable AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: gold, brightness: Brightness.dark),
        scaffoldBackgroundColor: const Color(0xFF080808),
        useMaterial3: true,
        cardTheme: CardThemeData(color: const Color(0xFF171717), elevation: 0),
        appBarTheme: const AppBarTheme(backgroundColor: Color(0xFF080808)),
      ),
      home: const ProjectCatalogScreen(),
    );
  }
}

class ProjectCatalogScreen extends StatefulWidget {
  const ProjectCatalogScreen({super.key});

  @override
  State<ProjectCatalogScreen> createState() => _ProjectCatalogScreenState();
}

class _ProjectCatalogScreenState extends State<ProjectCatalogScreen> {
  String search = '';

  @override
  Widget build(BuildContext context) {
    final results = domains.where((domain) {
      final text = '${domain.title} ${domain.details} ${domain.code}'.toLowerCase();
      return text.contains(search.toLowerCase());
    }).toList();

    return Scaffold(
      appBar: AppBar(title: const Text('Unthinkable AI')),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 900),
            child: CustomScrollView(
              slivers: [
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(children: [
                          CircleAvatar(child: Text('SM')),
                          SizedBox(width: 12),
                          Expanded(child: Text('Santa Muerte — slot na assety właściciela')),
                        ]),
                        const SizedBox(height: 16),
                        const Text('Katalog funkcji • 27 obszarów', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
                        const SizedBox(height: 6),
                        const Text('Prototyp. Wymagania źródłowe: requirements/user-directives.psv i requirements/source-candidates.psv. Tylko wymienione jako działające moduły mają implementację.'),
                        const SizedBox(height: 16),
                        TextField(
                          key: const Key('search_domains'),
                          decoration: const InputDecoration(
                            labelText: 'Szukaj modułu',
                            prefixIcon: Icon(Icons.search),
                            border: OutlineInputBorder(),
                          ),
                          onChanged: (value) => setState(() => search = value),
                        ),
                      ],
                    ),
                  ),
                ),
                SliverList.builder(
                  itemCount: results.length,
                  itemBuilder: (context, index) {
                    final domain = results[index];
                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
                      child: Card(
                        child: ListTile(
                          leading: Icon(domain.icon, size: 26),
                          title: Text(domain.title),
                          subtitle: Text('${domain.details} • ${domain.requirements} wymagań'),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () => Navigator.of(context).push(MaterialPageRoute<void>(
                            builder: (_) => DomainScreen(domain: domain),
                          )),
                        ),
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class DomainScreen extends StatelessWidget {
  const DomainScreen({required this.domain, super.key});
  final FeatureDomain domain;

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(domain.title)),
    body: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(domain.icon, size: 52),
        const SizedBox(height: 16),
        Text(domain.details, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 12),
        Text('ID domeny: ${domain.code}. Wymagania: ${domain.requirements}.'),
        const SizedBox(height: 12),
        const Text('Status: specyfikacja — oczekuje na implementację i testy.'),
        const SizedBox(height: 12),
        const Text('Rejestr źródłowy: requirements/requirements.csv'),
        if (domain.code == 'VIDEO') ...[
          const SizedBox(height: 20),
          FilledButton.icon(
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute<void>(builder: (_) => const FilmStudioScreen()),
            ),
            icon: const Icon(Icons.view_timeline_outlined),
            label: const Text('Otwórz studio scen i ujęć'),
          ),
        ],
      ]),
    ),
  );
}
