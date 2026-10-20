# VisionStory — czwarta partia VS-010–VS-012

**Data analizy:** 2026-10-20. **3 nowe pliki PDF / 22 strony.** Wcześniej VS-001–VS-009: 9 plików, 50 stron. Łącznie: **12 dokumentów, 72 strony**. Kolejny identyfikator źródła: **VS-013**. Źródła rejestrowane są wraz z oryginalną nazwą, liczbą stron i SHA-256 w \`requirements/visionstory_sources.csv\`.

Wszystkie 22 strony przeanalizowano. Poniższe ograniczenia rozdzielają rzeczywiście istniejący kod od wymagań samego dostawcy. Skróty z tłumaczonych polskich PDF nie są prawdziwymi ścieżkami API. Zweryfikowano angielskie ścieżki z dokumentacją \`developers.visionstory.ai\`.

## VS-010 — AI Avatar API — VisionStory.pdf (5 stron, SHA-256 959fc5ed...)

| Strona | Ustalenie źródła | Mapa funkcji, weryfikacja |
|---|---|---|
| 1 | \`GET /api/v1/avatars\`, \`POST /api/v1/avatar\`, \`POST /api/v1/avatar/framing\` oraz \`DELETE /api/v1/avatar\`; własne i publiczne awatary | Backend już ma listowanie, tworzenie i kadrowanie; celowo nie dodano usuwania bez zgody właściciela |
| 2 | Własne i publiczne listy osobno, \`is_public\`, paginacja \`cursor/limit\`, \`next_cursor=0\`; własne \`framing\`, publiczne \`framing=null\`, \`default_voice_id\` | Istnieje backend listowania/paginacji; UI powinien przełączać kolekcje i odczytywać domyślny głos z katalogu |
| 3 | Awatar ze zdjęcia: URL HTTPS **albo** inline base64, 10 MB, JPEG/PNG/WEBP/HEIC; najlepiej frontalny portret | Istnieje \`POST /api/cinema/visionstory/avatars/create\` z weryfikacją źródła i zgody osoby; Flutter ma formularz importu |
| 4 | Kadrowanie: \`avatar_id\`, \`aspect_ratio\`, \`zoom>=1\`, \`offset_x/y\` od -1 do 1, tylko własny awatar; \`framing_unavailable\` i dostawcy \`max_zoom\` | Backend \`/avatars/framing\` weryfikuje właściciela; do UI należy dodać diagnostykę zbyt małego zdjęcia / \`max_zoom\` i bezpieczny podgląd dla trzech formatów. Obecna bramka dodatkowo ogranicza zoom do 4 — lokalny limit, nie limit producenta |
| 5 | Usuwanie dotyczy wyłącznie własnego awatara, już gotowe wideo zostaje | Usuwanie niewdrożone celowo: właściciel nie wydał indywidualnej zgody na operację destrukcyjną |

## VS-011 — Voice Cloning API — VisionStory.PDF (5 stron, SHA-256 0b7c825b...)

| Strona | Ustalenie źródła | Mapa funkcji, weryfikacja |
|---|---|---|
| 1 | \`GET /api/v1/voices\`, \`POST /api/v1/voice\`, \`DELETE /api/v1/voice\`, własne i publiczne głosy | Backend oferuje katalog głosów i klonowanie; endpoint DELETE świadomie pominięty |
| 2 | BCP-47 locale i provider case-insensitive, limit/cursor, \`public_voices\`, \`my_voices\` (własne tylko na pierwszej stronie), preview URL i metadane | Istnieje \`/voices?locale=...&provider=...&limit=...\`; do UI: przełącznik grup, odtwarzanie preview, filtrowanie regionalne |
| 3 | Jeden próbny głos, URL HTTPS **albo** inline base64, opcjonalny \`preview_text\`; synchronizacja ok. 15 s; AVI/MP3/MP4/M4A/WAV do 30 MB | Backend \`/voices/clone\` wymaga zgody właściciela głosu; lokalne inline ograniczono do **14 MB** i na mobilnym pickerze do **8 MB**, co **nie pokrywa** maksimum dostawcy 30 MB. Wymagany upload strumieniowy do osobnej trwałej biblioteki (lub zgodny URL) |
| 4 | Klon używany w \`text_script.voice_id\` lub \`audio_script.voice_change=true\`; usunięcie nie usuwa dawnych filmów | Ścieżki backendu text i audio obsługują voice ID; operacja DELETE nie jest wywoływana automatycznie |
| 5 | Referencje: awatary, quickstart, TTS i BCP-47 | Kontrola zależności głos→awatar i język w UI, nie obietnica klonowania każdej próbki |

## VS-012 — AI Video Generation API — VisionStory.PDF (12 stron, SHA-256 c4cbc08d...)

| Strona | Ustalenie źródła | Kod i otwarte luki |
|---|---|---|
| 1 | Seedance, Wan i Kling; Pro+, discovery, wycena, generacja | Backend zawiera \`GET models\`, \`GET cost\`, \`POST ai_video\`; działanie na kontach Pro+ nie zostało potwierdzone |
| 2 | \`GET /ai_video\` (do 20 ID), \`GET /ai_videos\`, \`POST /asset\`, \`GET /assets\`, DELETE zasobów; start zwraca \`video_id/status/cost_credit\` | Dodano batch poll do 20 ID; asset upload/list już istniał; żadnego automatycznego DELETE |
| 3 | Katalog modeli, Seedance 2.5/2.0/Fast/Mini, Wan 3.0/Prime, Kling 3.0/Omni; limity czasu/rozdzielczości/specyficznych kombinacji | Bramka waliduje parametry z **żywego** katalogu i jawnie najważniejsze wyjątki; nie kodować na stałe cen i list modeli |
| 4 | 480p tylko Seedance/Wan; koszt pobierany przed submit, zwrot kredytów przy failed (deklaracja dostawcy) | Istnieje endpoint /ai-video/estimate i limit zatwierdzonego budżetu; refund nie został sprawdzony na faktycznym koncie |
| 5 | Różne ceny za sekundy i rozdzielczość; media w trzech formach URL, inline, asset ID | Backend pozwala na \`asset_id\`, inline i określone ścieżki uploadu; niezaufane URL do renderowania mają zostać najpierw zaimportowane do własnej biblioteki |
| 6 | Obrazy 30 MB, filmy 100 MB, audio 15 MB (Seedance); text/frame/refs warianty wzajemnie wykluczające | Bramka ma mniejsze limity inline; wsparcie dużych uploadów filmowych 100 MB wymaga obsługi strumieniowej, walidacji fps/wymiarów i magazynu |
| 7 | Wan: refs nie łączy się z aspect_ratio; Kling 3.0: bez refs, first_frame bez aspect_ratio; Kling Omni: bez first_frame i z video refs wymusza generate_audio=false | Dodano preflight przed płatną wyceną, kontrolę rodzaju \`asset_id\` we własnej bibliotece przy Kling Omni; zachowano odkrywanie model-aware |
| 8 | Pojedynczy status lub do 20 \`video_ids\`, queued/creating/created/failed; filtr listy statusów | Dodano \`POST /api/cinema/visionstory/ai-video/batch-status\` jako read-only; statusy bez płatnych operacji |
| 9 | Wykrywanie zajętości: \`status=queued,creating\`, przejście wszystkich cursorów; HTTP 429 concurrency z \`details\` jako object lub JSON string; brak rezerwacji slotu | Adapter odczytuje \`limit\` i \`in_flight\` z obu reprezentacji, lecz nie próbuje automatycznie ponawiać płatnego joba |
| 10 | Biblioteka wielokrotnego użytku, \`POST /asset\`, \`GET /assets\`, rodzaje image/video/audio, deduplikacja u dostawcy | Backend asset upload/list, ale uploader mobilny limituje mniej niż dostawca; brak produkcyjnego asset store per-tenant |
| 11 | Errory 30610/30301/37101–4/37110/37111, synchroniczne odrzucenie oraz failed asynchroniczne, refund | Nie każde odrzucenie to awaria serwera; dalsze prace nad precyzyjnym mapowaniem kodów 403 i UX refund/status |
| 12 | 180 wywołań/60s, polling 5–10s, 24h idempotencja, brak webhooków, media archiwizować, beta API | W repo istnieje \`services/visionstory/jobs.py\` (trwały, lecz single-owner ledger), backend MP4 archive; brak produkcyjnego RBAC wielu użytkowników i końcowej weryfikacji operatora |

## Stan implementacji / decyzje

| Integracja | Bieżący kod / testy | Kolejny etap |
|---|---|---|
| Portrait avatar create + framing | Backend + prototyp Flutter + testy mock | Lepszy preview zoom/offset, max_zoom errors |
| Voice clone | Backend + Flutter + test mock | Streaming large audio do 30 MB, min. długość i detekcja pojedynczego mówcy |
| Asset upload / list | Backend + Flutter | Duże filmy do 100 MB, źródło HTTPS po autoryzacji, per-tenant storage |
| AI video estimate / submit / job store | Backend i testy mock, trwały ledger w trybie single-owner | Provider live read-only, konto i kredyty, automatyzacja bez podwójnego obciążenia |
| Model-specific Wan/Kling guards | Nowy kod w \`services/visionstory/production.py\` | Regresja i profile dla przyszłych modeli |
| Batch poll 20 IDs | Nowy kod w client + production | Połączenie z Flutterem; harmonogram 5–10 sekund |
| Concurrency errors | Nowy parser object/string \`429\` w client | Wznowienie przez właściciela z tym samym request ID |
| Delete avatar / voice / video / asset | Nie wdrożono | Wyłącznie po osobnym poleceniu i potwierdzeniu, nie jest wymagane do produkcji kreatywnej |
| NLE, 123+ min, teledyski MP3 | Wciąż niepełne | Silnik montażu, praca wielu klipów, rendering i finalny odbiór |

## Nowe podwidoki do UI Studia Filmowego

| ID | Widok | Co ma zawierać |
|---|---|---|
| F-VS-13 | Awatar z portretu | Foto/URL, zgody, limit 10 MB, propozycja default_voice_id i aspekt |
| F-VS-14 | Kadrowanie dla 3 formatów | Osobny zoom, offset x/y, preview, limity, disabled framing, max_zoom błędy |
| F-VS-15 | Voice Clone Pro | Próbka (do 30 MB po obsłudze uploadu), prawa do głosu, preview_text, język, odsłuch i quota |
| F-VS-16 | Wybór silnika filmowego | Seedance 2.5/2.0, Wan 3.0, Kling 3.0/Omni — form fields dynamiczne według model capability API |
| F-VS-17 | References Library | Awatary, asset_id, obrazy/wideo/audio, typ referencji, czas, liczba, model-aware restrictions |
| F-VS-18 | Przedpłata i koszty | Czas, rozdzielczość, realny quote z API, max_approved_credits, sprawdzenie salda |
| F-VS-19 | Kolejka wielozadaniowa | Batch poll 20, queued/creating/created/failed, next_cursor, concurrency 429, retry z oryginalnym ID |
| F-VS-20 | Biblioteka MP4/zasobów | Archiwum 7 dni, import do NLE, zapis projektu, auth oraz status niedostępnego serwera |

To podwidoki do uzgodnienia z pełną mapą — nie zwiększa automatycznie liczby głównych ekranów. Materiały wizualne i ostateczny design dostarcza właściciel aplikacji.

**Zasady:** Nie uruchamiać płatnych generacji w CI. Nie oznaczać mocka jako produkcyjnej integracji z kontem. Nie udawać działania własnych renderów GPU. Nie przemycać kluczy dostawcy do Androida.
