# Unthinkable AI — zakres całej aplikacji

Decyzja właściciela (23.10.2026): Unthinkable AI to jedna wielomodułowa aplikacja i własny ekosystem. **Studio Filmowe jest tylko jednym** z 27 obszarów, a nie całą aplikacją ani zamiennikiem wszystkich pozostałych modułów. Dokumenty VisionStory służą jako wzorzec funkcji do samodzielnego stworzenia, nie jako obowiązkowa płatna integracja.

Rejestr źródłowy: requirements/requirements.csv (339 ID / 27 domen). Rejestr jest zakresem wymagań, nie listą ukończonych funkcji. Główna lista dla projektanta UI: docs/UI_SCREEN_INTEGRATION_MASTER.md.

| Domena | Zakres produktu |
|---|---|
| FOUND | Centrum, Santa Muerte, ustawienia, i18n |
| MODELS | Własne modele GGUF/safetensors, BYOM, inferencja |
| REASON | Rozumowanie, wiedza, pamięć, RAG |
| AGENTS | Agent Builder, agenci Code/NoCode i orkiestracja |
| EXT | Tool/Skill/Plugin Builder, OMAs/OMAt i adaptory MCP |
| DEEP | Deep Research, źródła, dowody, eksperymenty |
| DGM | DGM i RSI z walidacją i rollback |
| GITHUB | Automatyzacja pracy w repozytoriach i CI |
| IMAGE | Własne Studio Obrazu i modele edycji |
| VIDEO | Własne Studio Filmowe: awatary, referencje, własne wideo i NLE |
| AUDIO | Audio, MP3, głosy, TTS/STT, muzyka |
| GAME | Game Builder 2D/3D Code/NoCode |
| APPS | App Builder i środowisko IDE |
| PUBLISH | Ebooki, audiobooki, komiksy, bajki, roleplay |
| CHAT | Komunikator, pokoje QR, aliasy i legalna telefonia |
| BROWSER | Clearnet/Tor, przeglądanie i research |
| ANDROID | Opiekun Androida i uprawnienia |
| WEB | Scraper, API Wrapper, Website Creator NoCode |
| OWNER | Prywatny Vault, SFTP/SMB/Drive, sandbox |
| MATH | Millennium Problems, Cain's Jawbone |
| MARKET | Marketplace agentów, modeli i rozszerzeń |
| PAY | Plany, rozliczenia, płatności |
| INFRA | Własna infrastruktura, kolejka, GPU, bezpieczeństwo |
| FORMAL | Formalne dowody i solvery |
| LEGAL | Licencje, uprawnienia, audyt, ochrona danych |
| OPTION | Opcje z dokumentów wymagające decyzji właściciela |
| REUSE | Audyt i legalne wykorzystanie wcześniejszych repozytoriów |

## Własne Studio Filmowe — tylko domena VIDEO

Korzysta ze wspólnych modułów MODELS, IMAGE, AUDIO i INFRA, ale nie pochłania ich niezależnych funkcji ani ekranów.

Domyślna ścieżka: projekt → scenariusz → referencje i awatary → ujęcia z naszych modeli → oś czasu NLE → dźwięk i MP3 → render → MP4 → biblioteka. **Wszystkie podstawowe funkcje docelowo wykonujemy na własnym sprzęcie** lub na własnych, autoryzowanych workerach GPU; bez konta i kredytów VisionStory.

Co istnieje w kodzie: własny backend FFmpeg w services/film_studio oraz services/cinema/owned_studio.py, lokalne scenopisy i ekrany Flutter do importu, montażu i eksportu. Co nadal wymaga implementacji i testów: realna inferencja Wan/ODYN/LTX, pełny NLE, synteza awatarów, face swap za zgodą, lip-sync, beat detection do MP3, wielohostowa kolejka, izolacja danych użytkowników.

Historyczne API VisionStory jest wyłączone w głównym gateway, chyba że administrator wyraźnie włączy UNTHINKABLE_ENABLE_LEGACY_VISIONSTORY=1. Dla użytkownika końcowego nie jest częścią standardowego Studia Filmowego.

## Zasady pracy i UI

Dla każdego otrzymanego dokumentu: przypisz funkcje do odpowiedniej domeny, porównaj z repo, implementuj brakujące bezpieczne możliwości i testuj. Dokumentacja pojedynczego dostawcy NIE ogranicza 27 domen aplikacji. Status prototypu, backendu, lokalnego modelu i produkcyjnego E2E należy podawać osobno. Docelowy wygląd i grafiki projektuje właściciel; nie zastępuj ich własnymi assetami.

Regresja: tests/test_product_scope.py; mechanizm domyślnego wyłączenia zewnętrznych providerów testowany oddzielnie.
