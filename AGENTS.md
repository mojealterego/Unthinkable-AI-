# Unthinkable AI — AGENT ENGINEERING RULES

Repozytorium: mojealterego/Unthinkable-AI-; bazowa gałąź: main. Żadnych innych gałęzi bez decyzji właściciela.

1. Zawsze najpierw czytaj aktualny kod, README, docs/SOURCE_AUDIT.md i requirements/requirements.csv. Macierz 339 ID jest minimalną podstawą audytu, nie zapewnieniem implementacji.
2. Zbieraj dokładne źródła, wersje/licencje, komendy testów, artefakty dowodowe i SHA. Nie pomijaj ani nie zamieniaj wymagań bez decision log.
3. Nie ogłaszaj produkcyjności ani ukończenia bez rzeczywistego kompilatora, testów, logów i odbioru. Nie traktuj dekompilacji cudzej APK jako licencjonowanego źródła.
4. Do kodu pisz najmniejsze bezpieczne commity. Przed zapisem sprawdzaj HEAD i stosuj optimistic locking; unikaj uszkodzenia równoległych zmian.
5. DGM/RSI może sam wykrywać problemy i przygotowywać poprawki, ale rollout, uprawnienia do sekretów, produkcyjne płatności i zmiany krytyczne wymagają niezależnej walidacji i polityki akceptacji.
6. Przewiduj brak dostępu do GPU, praw do modeli, pieniędzy i uprawnień Android. Zamiast fikcyjnych wyników oznaczaj BLOCKED.
7. Model uncensored/abliterated/NSFW to profil modelu i dystrybucji; nie obejście przepisów ani zabezpieczeń małoletnich.
8. Dowolny alias telefoniczny może być identyfikatorem wewnętrznym; publiczny numer i caller ID wymagają realnego przydziału/weryfikacji.
9. Tor ma chronić prywatność, ale nie gwarantuje anonimowości. Nie realizuj nadużyć numerów, deanonimizacji czy nieautoryzowanego scrapingu.
10. Preferowane granice: Flutter/Dart frontend, Rust policies/runtime, C++ inference FFI, Python research/workers, cloud GPU queues, signed extensions, audytowane MCP adapters.

Systemowe wyniki każdej iteracji: zmienione pliki, SHA, testy, źródła, niezaliczone kryteria, zmapowane requirement IDs i następne zadania.

## Obowiązkowa zasada ciągłego wzbogacania systemu (polecenie właściciela, 2026-10-19)

**Każdy nowy dokument, PDF, opis API, repozytorium lub polecenie użytkownika jest wejściem do procesu implementacji, nie tylko do raportowania.**

1. Analizuj źródła po kolei i strona po stronie, nadaj trwały identyfikator oraz przypisz każdą nową funkcję do zakresu wymagań i odpowiednich ekranów UI. Zachowaj oryginalne nazwy kontraktów API i oddzielaj oficjalne schematy od propozycji.
2. Porównaj każdą funkcję z rzeczywistym kodem bieżącego `main` i wynikami CI. Oznacz `EXISTS_VERIFIED`, `PARTIAL`, `MISSING`, `BLOCKED` albo `DUPLICATE` wraz z dowodem. Nie uznawaj obecności karty UI za wdrożoną funkcjonalność.
3. **Dla `MISSING` i `PARTIAL` automatycznie implementuj bezpieczną, możliwą do zweryfikowania brakującą funkcję**. Obejmij kod, migracje danych, testy jednostkowe/integracyjne, podłączenie backendu do ekranu, aktualizację dokumentacji i mapy UI. Nie ograniczaj się do zadań w Roadmapie.
4. Wprowadzaj niezależne, małe zmiany na `main` i sprawdzaj konflikty HEAD przy każdej publikacji. Nie nadpisuj równolegle powstałych modułów; najpierw scalaj i uruchamiaj testy regresji.
5. Jeśli integracja wymaga brakującego klucza API, konta, limitu GPU, praw do danych, licencji lub dostępu infrastrukturalnego — wykonaj wszystkie dostępne niepłatne kroki, przygotuj bezpieczny adapter i testy z atrapą dostawcy, a resztę oznacz `BLOCKED` z konkretną zależnością. Nie wpisuj sekretów do czatu/repozytorium ani nie wykonuj płatnych operacji bez zgody.
6. Z każdym dokumentem ulepszaj architekturę i ergonomię, kiedy jest ku temu uzasadnienie techniczne; nie wymagaj nowego pytania właściciela przy zwykłych ulepszeniach kodu. Odróżniaj je od zmian wymagających rzeczywistej autoryzacji lub nowego wydatku.
7. Właściciel dostarcza finalny wygląd i grafiki UI oddzielnie. Aktualizuj od razu nazwy ekranów, wejścia/wyjścia, zależności, stany i sloty assetów; nie zastępuj autorskiego projektu przypadkowymi grafikami.
8. Nie ogłaszaj zakończenia całego produktu, dopóki pełny audyt źródeł, integracja i odbiór nie są potwierdzone. Po każdej iteracji podawaj dokładne commity, testy CI, brakujące funkcje i blokady.

Dla VisionStory szczegóły źródłowe i rozszerzenia znajdują się w `requirements/visionstory_sources.csv`, `docs/VISIONSTORY_BATCH_02_AUDIT.md` oraz `docs/UI_SCREEN_INTEGRATION_MASTER.md`. Dokumentacja jest otwarta — użytkownik zapowiedział co najmniej 60 kolejnych plików.


## Product owner correction: LOCAL-FIRST / BYOM / UNCENSORED

**The user owns the Unthinkable AI ecosystem. External vendors (VisionStory etc.) are references for feature requirements, NOT the platform's main production backend.**
1. Primary offer: **Bring Your Own Model** — import user-owned GGUF and safetensors, select task class (LLM/image/video/audio), label Standard/Uncensored/Abliterated and run with the user's choice of locally installed or self-hosted engines, respecting the individual checkpoint license.
2. No external vendor account, token, credits or subscription may be a prerequisite for basic app operation or using supported local models. No default external API or upload. A vendor adapter is separately opt-in, not an app core dependency; do not divert product development toward provider account setup.
3. The default chat target is an on-device loopback llama.cpp-compatible HTTP server without credentials. Remote user-owned inference is opt-in and TLS-authenticated. Do not confuse file import with having a working native inference runtime.
4. Own inference architecture targets: Android native runtime where technically supported, user-controlled workstation/cloud GPU for large diffusion/video models, secure model registry/provenance/quantization, offline files and projects. No hidden remote execution. Vendor-provided public APIs are auxiliary and not evidence that Unthinkable runs those model weights.
5. Model profile is metadata for selection and UI; it must not misrepresent actual model internals. Treat uncensored/abliterated as technically supported user model variants, not as a guarantee of unlimited output. Follow age and legal protections.
6. When reading third-party docs, extract **capabilities, workflows and UX requirements**, implement independently in the Unthinkable product using owned/self-hosted components whenever possible, and clearly label capabilities still blocked on local engine/GPU/codec.
7. UI roadmap priority: My Models > Local Chat > Image Generation > Film Studio > Audio > Builders, then optional external adapters.


## Zakaz uzależniania własnego Studia Filmowego od dostawcy (decyzja 2026-10-23)

Dokumentacja VisionStory stanowi materiał porównawczy funkcji, nie kontrakt usługowy. Studio Filmowe Unthinkable AI musi korzystać z własnych modeli, własnych pracowników GPU, własnej biblioteki zasobów, FFmpeg/NLE i własnej infrastruktury. Konto, klucz i kredyty VisionStory nie są częścią domyślnego produktu. Historyczny kod adaptera dostawcy może pozostać nieaktywny do regresji, ale nie stanowi ścieżki implementacji wymagań. Przy każdym nowym dokumencie rozwijaj nasze silniki oraz realne ekrany użytkownika, nie odpłatne integracje stron trzecich. Nie oznaczaj FFmpeg jako gotowego generowania Wan/ODYN bez prawdziwego modelu i testu.

## PRODUCT SCOPE GUARD — 2026-10-23

Unthinkable AI is a multi-module platform. Film Studio is exactly ONE of its 27 product domains, not the whole application. Preserve all 27 UI product domains in lib/main.dart, their distinct responsibilities, and the global UI/integration inventory.

VisionStory and other vendor PDFs are sources of functional requirements for our own implementation; they are not an authorization to copy proprietary internals and do not make vendor accounts, credits, keys or APIs prerequisites for our film studio. The default VIDEO entry points to our film engines in services/film_studio and services/cinema/owned_studio.py and to our project/asset interfaces. Vendor compatibility is historical optional functionality, disabled by default.

Keep IMAGE, AUDIO, MODELS, AGENTS, GAME, APPS, WEB, CHAT, MARKET, PAY and all other domains independent; use shared first-party asset/model/worker layers instead of collapsing them into a video-specific product. Do not claim that FFmpeg assembly is AI generation or complete NLE. Always show verified delivery versus missing native inference, rendering, rights and infrastructure blockers.

Full product contract: docs/PRODUCT_SYSTEM_SCOPE.md. Regression: tests/test_product_scope.py.
