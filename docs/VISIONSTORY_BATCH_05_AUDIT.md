# VisionStory — partia V: VS-013–VS-015 (26 stron)

Data: 2026-10-20. Trzy pliki: 4 + 13 + 9 = 26 stron. Poprzednio VS-001–VS-012: 72 strony. Razem 15 plików / 98 stron. Następne ID: VS-016. Źródła z SHA-256 w requirements/visionstory_sources.csv.

## VS-013 — Structured Media Understanding API — VisionStory.PDF

| Strona | Ustalenie źródła | Odwzorowanie / brak |
|---:|---|---|
| 1 | 1 | POST /api/v1/media/understand, prompt 1–5000, inputs 1–8 i top-level JSON Schema object | Backend istnieje; nowy formularz Flutter korzysta z asset_id |
| 2 | 2 | JPEG/PNG/WebP/BMP/TIFF/GIF, WAV/MP3, MP4/MOV; SDK 180s; CLI understand-media | UI przesyła asset_id, backend dopuszcza dodatkowe typy media |
| 3 | 3 | Local/remote MCP; remote tylko URL i asset_id; data.output/usage/cost_credit, 37100, brak retry timeoutu | Jawna zgoda na koszty, JSON i użycie kredytów. Nie uruchamiaj retry płatnego timeoutu |
| 4 | 4 | Linki do STT/Assets/Agents | Bez odrębnego endpointu |


## VS-014 — VisionStory CLI.PDF

| Strona | Ustalenie źródła | Odwzorowanie / brak |
|---:|---|---|
| 1 | 1 | Python 3.10+, visionstory-cli, izolowany uv, macOS/Linux/WSL | Nie instalować automatycznie w Androidzie |
| 2 | 2 | Instalator/PyPI, --help, zamaskowany login, status 401 | Instalacja wymaga hosta i klucza właściciela |
| 3 | 3 | doctor, update, logout, uninstall, version | Nowy skrypt CLI preflight ograniczony do doctor/contract/credits |
| 4 | 4 | Avatar+głos → film MP4, status, bez automatycznych aktualizacji | Integracja filmowa ma API Flutter+backend, bez testu live provider |
| 5 | 5 | VISIONSTORY_API_KEY; custom API_BASE; owner-only config | Klucz pozostaje poza APK; blokada niezatwierdzonego API base w diagnostyce |
| 6 | 6 | doctor offline, credits read-only, base-url i timeout | Preflight dopuszcza odczyt kredytów tylko po jawnym uruchomieniu |
| 7 | 7 | Custom host może otrzymać X-API-Key; rozdział base-url i download URL | Ważne ryzyko eksfiltracji klucza do obcej domeny |
| 8 | 8 | models/avatars/voices/credits/videos/assets; dokładnie jedno z text/audio | Backend katalogów i walidacja trybów istnieją |
| 9 | 9 | --output/--no-wait, media CRUD, DELETE nieodwracalne | Brak automatycznego usuwania |
| 10 | 10 | Paginacja awatarów, BCP-47, TTS, transcribe i diarization | Backend istnieje, UX pozostaje częściowy |
| 11 | 11 | align, image models, AI video cost/create/status | Backend istnieje, konta live nie sprawdzono |
| 12 | 12 | Zaawansowane payloady JSON, contract fingerprint i exit codes | Skrypt sprawdza contract bez logowania wyników |
| 13 | 13 | understand-media, TTS rate; 180s sync, płatność za sukces | Dedykowany ekran JSON i zabezpieczenie przed ponowieniem |


## VS-015 — VisionStory API for AI Agents(1).PDF

| Strona | Ustalenie źródła | Odwzorowanie / brak |
|---:|---|---|
| 1 | 1 | MCP/CLI/SDK/Skill/llms.txt/OpenAPI, wspólny klucz | REST adapter nie oznacza działającego MCP |
| 2 | 2 | Agent Skill i 28 public operations MCP/SDK/CLI | Liczbę operacji trzeba weryfikować OpenAPI w danym wydaniu |
| 3 | 3 | uvx visionstory-mcp --check, get_credits/list_models | Preflight sprawdza tylko już zainstalowany binary MCP |
| 4 | 4 | Remote Streamable HTTP /mcp, brak dostępu do lokalnych plików | Potrzebny osobny podłączony host i obsługa autoryzacji |
| 5 | 5 | Release resource i typed Python SDK | CLI/Skill jeszcze nie zainstalowano na docelowym środowisku |
| 6 | 6 | npx skills add, możliwe Snyk W011, helper Skill != pełne MCP | Wymagana inspekcja źródeł/licencji przed instalacją |
| 7 | 7 | llms.txt, llms-full.txt, OpenAPI i workflow avatar→video→MP4 | Backend obsługuje części, nie pełny nadzorowany agent |
| 8 | 8 | Klucz prywatny, realne IDs, idempotencja, polling >=5s, brak DELETE bez zgody | Istnieje ledger zadań single-owner |
| 9 | 9 | Remote media tylko URL/asset_id, local także inline_data | UI JSON korzysta z asset_id; nie twierdzi, że remote MCP podłączono |


## Relacja do wcześniejszych dokumentów

VS-015 jest angielskim odpowiednikiem i poszerzeniem tematyki wcześniejszego VS-006 (polski, 8 s.). PDF-y mają inne hashe, długości i układ stron; nie są kopiami bitowymi. Zachowujemy osobne ID, lecz wymagania o REST, MCP i bezpieczeństwie nie są liczone podwójnie.

## Implementacja i dowody

| Funkcja | Kod i bieżący status | Otwarte zależności |
|---|---|---|
| Media Understanding REST (1–8 mediów, JSON schema, koszt) | services/visionstory/router.py, testy mock | Live account + provider key + kredyty |
| Formularz analizy mediów Flutter | lib/features/video/visionstory_understanding_screen.dart i nawigacja z Zasobów | Odbiór CI Flutter + docelowy UI właściciela |
| CLI/MCP read-only preflight | tools/visionstory_cli_preflight.py; testy | Instalacja w zaufanym Linux środowisku, lokalny sekret, podłączenie MCP |
| API przez SDK/CLI i 28 operacji | Fragmenty funkcji REST istnieją | Pełna enumeracja aktualnego OpenAPI i permission registry |
| Remote MCP /mcp | Udokumentowana różnica inline vs URL/asset_id | Niepodłączony endpoint i RBAC dla tenantów |
| NLE 123+, MP3→teledysk | Nieukończone | Renderer, magazyn plików i montaż |

**Bezpieczeństwo:** brak automatycznego install/uvx z niezweryfikowanego źródła, brak DELETE, brak logowania kluczy i base64. Skrypt CLI wykonuje tylko doctor/contract i na życzenie credits. Wynik CI z mockami nie potwierdza żywej usługi ani wydanych kredytów.

## Integracje UI

F-VS-21: prompt, 1–8 asset IDs, JSON Schema, rights/credits consent, output JSON + usage + cost. F-VS-22: operator CLI doctor/contract/credits. F-VS-23: local versus remote MCP, permissions, vendor Skill. F-VS-24: moderation 37100, concurrency, brak auto-retry i koszt tokenów. Są to podwidoki Studia Filmowego, a nie automatycznie cztery nowe globalne ekrany.
