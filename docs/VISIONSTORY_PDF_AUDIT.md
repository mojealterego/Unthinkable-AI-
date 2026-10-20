# VisionStory: audyt 12 dokumentów źródłowych (72 strony; dokumentacja otwarta)

Data: 2026-10-19. Dokumenty przekazane przez właściciela aplikacji:

- Generate video — VisionStory API.PDF (5 stron): szczegółowy kontrakt REST POST /api/v1/video, dwa alternatywne źródła skryptu, MIME audio i idempotencja.
- AI Video API for Developers — VisionStory.PDF (8 stron): REST, SDK, CLI, MCP, video job, katalogi funkcji i kredyty.
- AI Models for Video, Avatars, and Images — VisionStory.pdf (7 stron): oddzielne katalogi modelowe, V-Character, Seedance, Wan, Kling, Nano Banana, Seedream, GPT Image oraz limity.

Przeprowadzono porównanie z bieżącą dokumentacją developers.visionstory.ai. Tłumaczone do polskiego nazwy pól z PDF muszą być w kodzie zamienione na prawdziwe angielskie identyfikatory API.

## Zaimplementowane w gateway REST (nie aktywowane produkcyjnie)

| Funkcja | Endpoint / uwagi |
|---|---|
| Wideo z tekstu | POST /api/cinema/visionstory/talking-video, text i voice_id |
| Wideo z nagrania | Ten sam endpoint, audio_script: audio_url lub inline_data (base64, 8MB cap) |
| Denoise i voice_change | audio_script; potwierdzenie praw do nagrania |
| Tempo mowy | speech_rate normal / slow / fast |
| Emocje | cheerful / angry / marketing / news / singing |
| Tło pod chromakey | background_color #RRGGBB |
| Model V-Character | GET /api/cinema/visionstory/models |
| Model Seedance / Wan / Kling | GET /api/cinema/visionstory/models/ai-video; tylko katalog |
| Model Nano Banana / Seedream / GPT Image | GET /api/cinema/visionstory/models/image; tylko katalog |
| Publiczne awatary | GET /api/cinema/visionstory/avatars/public |
| Wideo w ostatnich zadaniach | GET /api/cinema/visionstory/videos/recent |
| Status i URL MP4 | GET /api/cinema/visionstory/talking-video/{video_id} |
| Ochrona kosztu | Zatwierdzenie paid generation, model z live katalogu, sprawdzenie credits |
| Sekrety | VISIONSTORY_API_KEY tylko na serwerze; osobny klucz gateway |

Wszystkie wywołania provider są mockowane w testach. Żaden klucz VisionStory nie został wpisany do repo ani ujawniony. Nie ma jeszcze działającego Flutter VisionStory UI, realnego generatora klipów Seedance/Wan/Kling czy MP3→teledysk, ani podłączonego renderera ODYN / montażowni 123+ minut.

## Lista podwidoków do projektu Studia Filmowego

- F-VS-08a: scenariusz tekstowy, głos, tempo i emocje.
- F-VS-08b: import MP3/WAV, alternatywny HTTPS audio URL, denoise i konwersja głosu za zgodą.
- F-VS-08c: avatar własny lub publiczny, kadrowanie, wybór chromakey.
- F-VS-03b: katalog modeli generatywnego wideo i limitów — Seedance, Wan, Kling.
- F-VS-03c: katalog modeli obrazowych i limitów — Nano Banana, Seedream, GPT Image.
- F-VS-10a: postęp queued / creating / created / failed; zapis video_id i client_request_id.
- F-VS-11a: biblioteka MP4, import do projektu, download przed 7-dniowym wygaśnięciem.

Są to podwidoki dotychczasowych ekranów Studia Filmowego, nie automatycznie nowe ekrany aplikacji. Grafiki właściciela i finalny UI pojawią się osobno.

## Zakres poza bieżącym adapterem

Należy dostarczyć: Android UI; trwałą bazę zadań i idempotency retry; przenoszenie pliku MP4 do bezpiecznego magazynu; płatności/licencje per-tenant; montaż wielościeżkowy; praca na ujęciach i referencjach; test na rzeczywistym koncie po dobrowolnym zatwierdzeniu kosztu. Wideo 123+ minut jest wynikiem składania ujęć, a nie jednego zadania V-Character. Publiczne katalogi nie oznaczają dostępności modeli na konkretnym koncie.

W źródłach dostawcy istnieje rozbieżność: przykładowy stan renderowania success vs deklarowane enum created; gateway normalizuje success do created. Okno powtórzenia tego samego client_request_id to 24 godziny, retencja dostawcy 7 dni.

## Partia II / dokumenty VS-004–VS-006

Pełna analiza 14 stron nowych PDF, ich unikalne wymagania, przypisania do UI, braki oraz dalsze procedury: [`docs/VISIONSTORY_BATCH_02_AUDIT.md`](VISIONSTORY_BATCH_02_AUDIT.md). Rejestr 6 plików: [`requirements/visionstory_sources.csv`](../requirements/visionstory_sources.csv). Zapowiedziano co najmniej 60 dalszych plików — nie wliczono ich do liczby przeanalizowanych.

## Partia III: VS-007–VS-009

Pełne 16-stronicowe rozpoznanie zmian API, duplikatu strony Overview i quickstart renderowania: [docs/VISIONSTORY_BATCH_03_AUDIT.md](VISIONSTORY_BATCH_03_AUDIT.md). Podwójny plik Overview2 ma dokładnie taki sam tekst stron 1–4 jak VS-004, ale pozostaje osobnym ID i checksum.

## Stan wdrożenia po 9 PDF-ach — 2026-10-20

To rejestr techniczny po przyrostowej implementacji; oznaczenie kodu nie jest potwierdzeniem dostępu do prywatnego konta VisionStory.

| Funkcja źródłowa | Wdrożenie | Testy / ograniczenia |
|---|---|---|
| Awatar mówiący (tekst lub MP3), modele, głosy i kredyty | Serwer `services/visionstory/router.py`, Flutter `visionstory_screen.dart` | Testy mock; prawdziwe konto niepołączone |
| Własne i publiczne awatary, kursory i katalogi | Odczyt, paginacja w routerze | Brak generatora nowego awatara, framing |
| Voice locale/provider filters | `services/visionstory/client.py` + router | CI backend zaliczony |
| Zapis gotowego MP4 | `services/visionstory/archive.py`, Flutter pobieranie | Wymaga operator allowlist CDN i trwałego wolumenu; brak RBAC wielu tenantów |
| TTS do MP3 | `services/visionstory/speech.py`, Flutter pobieranie | Test mock; płatne wywołanie za zgodą |
| STT, SRT niezależne od diarization, alignment | `services/visionstory/speech.py` i `production.py` | Endpointy za zgodą; testy mock |
| Seedance/Wan/Kling AI video — text, first-frame, refs | `services/visionstory/production.py` | Katalog live, quotation przez GET cost, zgoda na maksymalny koszt, status job; nie sprawdzono live |
| Model-aware video cost / credits | `services/visionstory/production.py` | Blokady niezgodnych parametrów modelu i przekroczonego budżetu |
| Provider image generation / custom avatars / voice cloning | NIE WDROŻONO | Kolejne adaptery i UI wymagane |
| Provider asset upload/list/delete (z wymaganą autoryzacją) | NIE WDROŻONO | Kontrakt API dostępny; należy dopisać kod i testy |
| MCP 28 operacji, lokalny/zdalny, Agent Skill | NIE WDROŻONO produkcyjnie | Wymaga pełnego katalogu operacji, kontroli uprawnień i zatwierdzenia instalacji |
| Trwały multitenant job store, reverse billing, NLE 123+ minut, audio→teledysk | CZĘŚĆ planowania / BRAK wykonania | Potrzebne projekty, magazyn, kolejka, silnik render/montaż i testy na infrastrukturze |

Wyniki zweryfikowane: [Backend CI 39339602721](https://github.com/mojealterego/Unthinkable-AI-/actions/runs/39339602721) SUCCESS; [Flutter Android CI 39340324150](https://github.com/mojealterego/Unthinkable-AI-/actions/runs/39340324150) SUCCESS dla wcześniejszej wersji ekranu. Nowszy build Flutter nadal wymaga końcowego potwierdzenia przed akceptacją. Brak dowodu renderowania na koncie użytkownika i brak użycia płatnych kredytów.

**Nie przyjmować kolejnej partii dokumentów jako zamknięcia zakresu, dopóki te pozycje MISSING i PARTIAL nie zostaną rozstrzygnięte i przetestowane.**

## Partia IV: VS-010–VS-012

Szczegółowa analiza **22 stron**, identyfikatory funkcji, stany kodu, dodatkowe wymagania model-specific, katalog referencji i lista podwidoków F-VS-13..20: [VISIONSTORY_BATCH_04_AUDIT.md](VISIONSTORY_BATCH_04_AUDIT.md). Wykaz dokumentów zawiera 12 pozycji, razem 72 strony; następny numer VS-013.
