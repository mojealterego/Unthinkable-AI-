# ADR-002 — Unthinkable AI jako własna, modułowa platforma

**Status:** obowiązujące założenie właściciela • 2026-10-23  
**Zakres:** cały produkt (27 domen wymagań i 18 grup interfejsu). Studio Filmowe = **jeden** moduł produktu.

## Decyzja

**Unthinkable AI nie jest usługą VisionStory, nakładką na VisionStory ani produktem filmowym z dodatkami.** Jest własną, szeroką platformą AI. Zewnętrzne dokumentacje VisionStory, innych API, repozytoriów, SDK, serwisów NoCode i narzędzi kreatywnych są materiałem do audytu **funkcji, ergonomii i interfejsów**. Ich kod, zamknięte modele, kredyty czy konta nie stają się automatycznie własnymi komponentami Unthinkable.

27 domen ewidencji źródłowej (339 bazowych wymagań): `FOUND, MODELS, REASON, AGENTS, EXT, DEEP, DGM, GITHUB, IMAGE, VIDEO, AUDIO, GAME, APPS, PUBLISH, CHAT, BROWSER, ANDROID, WEB, OWNER, MATH, MARKET, PAY, INFRA, FORMAL, LEGAL, OPTION, REUSE`.

Mapa UI ma **18 grup**, 141 planowanych ekranów/widoków w podstawowym zestawieniu. Grupy UI nie odpowiadają jeden-do-jednego domenom wymagań. Ich liczba może rosnąć w toku analizy kolejnych dokumentów. Każdy moduł ma własny punkt wejścia, kontrakt możliwości i rzeczywiste stany gotowości.

## Własny rdzeń techniczny

- **UI aplikacji:** Flutter/Dart, właściciel przygotowuje finalne widoki i grafiki Santa Muerte. Czat, modele, WWW, agenci, obraz, film, audio, Game/App Builder, komunikacja, marketplace, badania i administracja są równorzędnymi domenami.
- **Runtime modeli:** import GGUF/safetensors, kontrola licencji/hashy, własne silniki lub własny serwer GPU, planowane Rust + C++ FFI, lokalny i self-hosted inference. Import modelu **nie jest** równoznaczny z działającą inferencją.
- **Studio Filmowe:** własny projekt → własne materiały/referencje → własne modele/generatory i moduły awatarów → edycja NLE/FFmpeg → MP3/voice → własne renderowanie MP4 i magazyn. `services/film_studio/`, `services/cinema/owned_studio.py` i powiązane ekrany Flutter mają działający **podstawowy montaż FFmpeg**, ale natywne generowanie Wan/LTX/ODYN, lip-sync, podmiana twarzy, pełne NLE i długi film E2E wymagają jeszcze implementacji/testów.
- **Pozostałe moduły:** obowiązuje identyczny wymóg dowodowy (kod + testy + rzeczywista integracja); obecność widoku w katalogu nie oznacza ukończenia.
- **Zewnętrzne adaptery:** opcjonalne i odseparowane; nie stanowią domyślnych ścieżek wykonania, nie uzależniają aplikacji od klucza ani kredytów dostawcy. Są przydatne wyłącznie gdy właściciel **osobno** zechce z nich korzystać.

## Granica VisionStory — wymuszona w repo

Domyślny `services/gateway/app.py` nie rejestruje tras `/api/cinema/visionstory/*`. Historyczne adaptery REST pozostają jedynie pod jawnie ustawionym `UNTHINKABLE_ENABLE_LEGACY_VISIONSTORY=1`, np. dla testów regresji. **Zakaz:** nie przedstawiać historii implementacji tych adapterów jako ukończenia własnego generatora, Studia Filmowego lub kolejnych wymagań użytkownika.

Trasy własnego backendu: `/api/film-studio/*` i `/api/cinema/owned/*`, bez zależności od `VISIONSTORY_API_KEY`. FFmpeg to silnik montażu, nie model generatywny. Dwa istniejące prototypowe backendy filmowe należy w przyszłości scalić do jednego domenowego API i długoterminowej kolejki z bazą użytkowników oraz RBAC.

## Kryteria akceptacyjne

1. Domyślne `main` ujawnia trasy własnego Studia i **nie udostępnia** legacy VisionStory.
2. Aplikacja pokazuje wszystkie 27 domen źródłowych, a `VIDEO` jest jedną z nich; architektura produktu nie zmienia się w architekturę opłacanego providera.
3. W dokumentacji i UI rozróżnia się: działa kod montażu, działa inferencja, użyto konkretnego modelu, potwierdzono E2E; żaden poziom nie zastępuje następnego.
4. Testy i CI nie wymagają prawdziwych kluczy VisionStory, salda kredytów ani płatnej generacji.
5. Nowe dokumentacje dostawców przekłada się na niezależne funkcje i własne ekrany Unthinkable. Możliwość ponownego użycia biblioteki/modelu zależy od licencji, zgodności i realnego wykonania.

**Dowody:** `tests/test_platform_boundaries.py`; `tests/test_film_studio.py`; `tests/test_owned_cinema.py`; `docs/OWN_FILM_STUDIO.md`; `docs/UI_SCREEN_INTEGRATION_MASTER.md`. Brak GPU lub kluczy jest stanem BLOCKED, nigdy DONE.
