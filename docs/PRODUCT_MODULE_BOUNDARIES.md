# UNTHINKABLE AI — GRANICE MODUŁÓW I WŁASNOŚĆ ARCHITEKTURY

Stan polityki produktu: 2026-10-23. Dokument operacyjny wynikający z decyzji właściciela, nie dowód ukończenia implementacji.

## Główna zasada

**Unthinkable AI to wielomodułowa aplikacja Android-first i ekosystem własnych silników. Studio Filmowe jest jednym modułem, nie produktem nadrzędnym.** Żaden pojedynczy PDF, dostawca ani pakiet opisujący Studio nie zastępuje pozostałych obszarów. Własne środowisko wykonawcze ma obsługiwać user-owned modele, projekty, dane, renderery, procesy zadań i prywatną pamięć. Integracje osób trzecich są opt-in i mogą służyć wyłącznie jako pomocnicze adaptery, nigdy jako wymóg podstawowego produktu.

### Oficjalne domeny z głównego rejestru (27)

| Segment prac | Wymagania i granice |
|---|---|
| FOUND, LEGAL, OPTION | Tożsamość, i18n, dostępność, licencje, zgody, opcjonalne funkcje |
| MODELS, REASON, FORMAL | BYOM GGUF/safetensors, inferencja, pamięć, RAG, benchmarki, dowody |
| IMAGE, VIDEO, AUDIO | Własne silniki obrazu, Studia Filmowego i audio, współdzielona biblioteka assetów |
| AGENTS, EXT, DGM, GITHUB, REUSE | Agenci, Skill/Tool/Plugin/Agent Builder, kontrolowany rozwój DGM, repozytoria i CI |
| DEEP, MATH | Deep Research, matematyka, rozwiązania i weryfikowalne eksperymenty |
| GAME, APPS, WEB, PUBLISH | Game/App/WWW Code+NoCode, scraper, wrapper, edytory, wydawnictwo, książki |
| CHAT, BROWSER, ANDROID | Komunikator, publiczne numery od operatorów, aliasy wewnętrzne, Tor/Clearnet, opiekun Androida |
| OWNER, MARKET, PAY, INFRA | Prywatny workspace, marketplace, rozliczenia, worker-y, magazyn, bezpieczeństwo |

Dokładny rejestr: `requirements/requirements.csv` — początkowe 339 IDs (nowe dokumenty rozszerzają, nie zastępują wymagań). Mapę 141 ekranów w 18 grupach UI należy rozumieć jako **zakres makiet**, nie dowód działania funkcji. Dokument: `docs/UI_SCREEN_INTEGRATION_MASTER.md`.

## Sposób użycia zewnętrznej dokumentacji

- Analizować źródło dokument po dokumencie i rozdział po rozdziale, przypisywać jego funkcjonalności do odpowiedniej domeny Unthinkable.
- Najpierw sprawdzić nasze komponenty: istniejący kod, licencje, testy, możliwą adaptację. Brakujące funkcje implementować jako **własne** komponenty/adaptery do samodzielnego wykonania.
- Jeżeli model lub algorytm jest otwarty i licencja pozwala — uruchamiać go na własnym sprzęcie lub GPU. Nie kopiować zamkniętych implementacji ani nie udawać, że API dostawcy = lokalny model.
- Nie uzależniać Studio od kredytów VisionStory. Stare usługi `services/visionstory/` pozostają wyłączone domyślnie w `services/gateway/app.py`; historyczne testy uruchamiają je jawnie przez `UNTHINKABLE_ENABLE_LEGACY_VISIONSTORY=1`.
- Nie oznaczać komponentu jako DONE tylko dlatego, że istnieje przycisk, opublikowano dokument albo test mockowany przeszedł. Na status produkcyjny wymagane są sprawdzone realne wykonanie, bezpieczeństwo danych oraz dowody środowiska.

## Pierwszy moduł mediów i granica realizacji

WŁASNE STUDIO:
1. Backend `services/film_studio/` — import MP4/MP3/WAV/JPEG/PNG, walidacja timeline, montaż i soundtrack przez FFmpeg, kolejka podstawowych prac, output MP4.
2. Backend `services/cinema/owned_studio.py` — własne zasoby, cięcie, łączenie, soundtrack, identyfikatory projektów, kontrola praw i zatwierdzenie wykonania.
3. Flutter `lib/features/video/own_film_studio_screen.dart` — operacje na własnym serwerze, import i odbiór MP4, bez loginu VisionStory. Ekran VIDEO w `lib/main.dart` prowadzi tutaj domyślnie.
4. PLAN / BLOKADY: własny worker Wan/LTX/ODYN, pełne generowanie awatarów i twarzy, consented face-swap, lip-sync, beat detection, wielościeżkowy NLE z keyframes/VFX, render 123+ min potwierdzony soak testami, izolacja tenantów/RBAC i niezawodne recovery wielohostowe.

**FFmpeg montuje istniejące materiały; nie zastępuje modeli generatywnych.** Do dużych modeli potrzebny będzie zgodny checkpoint, legalna licencja, pamięć GPU i uruchamialny worker z testem rzeczywistego wideo. Własny serwer/GPU nie jest tym samym co zewnętrzny dostawca usług.

## Priorytety prac dla całej aplikacji

- P0: stabilna nawigacja 27 domen, rejestr wymagań i ewidencja źródeł, prawdziwe lokalne modele/inferencja, pierwsze własne media, wydawane artefakty Android, testy bezpieczeństwa.
- P1: wszystkie studia twórcze i kreatory Code/NoCode (WWW, agent, aplikacje, gry), integracje GitHub, naukowe Deep Research, komunikacja.
- P2: rozwinięty rynek i płatności, wieloagentowe DGM ze ścisłą polityką, skalowanie infrastruktury, zaawansowane produkcje filmowe. Priorytet nie jest pozwoleniem na usunięcie mniej zaawansowanej funkcji.

**Bez potrzeby pytania o zwykłe ulepszenia implementacyjne.** Zmiany wymagające środków finansowych, kluczy, uprawnień lub rzeczywistego wdrożenia infrastruktury należy oznaczyć jako BLOCKED do czasu autoryzacji.
