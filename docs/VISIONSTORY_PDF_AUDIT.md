# VisionStory: audyt 6 dokumentów źródłowych (34 strony; dokumentacja otwarta)

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
