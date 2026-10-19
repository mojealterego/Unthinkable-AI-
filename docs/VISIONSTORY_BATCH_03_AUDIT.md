# VisionStory — partia III, dokumenty VS-007–VS-009

Data audytu: 19 października 2026 r. Trzy nowe pliki: 5 + 4 + 7 = **16 stron**. Łącznie dziewięć przyjętych dokumentów (50 stron). Dalszych co najmniej 60 zapowiedzianych dokumentów nie otrzymano; nie zamykamy listy funkcji i ekranów.

## VS-007 — VisionStory API Changelog.pdf — 5 stron

| Strona | Dokumentacja | Stan Unthinkable AI |
|---|---|---|
| 1 | Wersja 0.0.13 (24 IX): status filters dla AI video, komunikaty concurrency, prompty Seedance do 5000 znaków; wersja 0.0.12: modele GPT Image i ceny wg rozdzielczości | Dodano read-only listę zadań AI z status filters, limit, cursor; generowanie Seedance i kalkulator kosztów pozostają niewdrożone |
| 2 | 0.0.11 Seedream 5 Lite/Pro, limity specyficzne dla modelu; 0.0.10 avatar pagination/framing; 0.0.9 media understanding i tempo TTS | Paginacja awatarów, media understanding i speech_rate już miały adapter; framing własnego awatara i generacja Seedream brak |
| 3 | 0.0.8 login/logout CLI, filtrowanie głosów BCP-47 locale i provider, stronicowanie, TTS, transkrypcje, usunięcie 480p dla nowych żądań | Dodano voice locale/provider/limit/cursor. Brak lokalnego CLI oraz TTS/STT |
| 4 | Poprawki MP3 Skill i regionalnych filtrów, transkrypcja SRT niezależna od diarization; 0.0.7 audio transcribe/align, głosy i aktywny plan Pro+, 24→26 operacji | SRT bez konieczności diarizacji należy wprowadzić w przyszłym ekranie; TTS/STT i instalacja MCP czekają. Nie mieszać historycznej liczby 26 ze zgłoszonym później katalogiem 28 |
| 5 | 0.0.6 workspace kluczy API, dokumentacja API; 0.0.4 uruchomienie portalu | Globalny prywatny klucz w backendzie; brak zarządzania kontem i kluczami per-tenant |

Weryfikacja publiczna: https://developers.visionstory.ai/guides/changelog i https://developers.visionstory.ai/guides/ai-video . Tekst w przesłanym PDF został przetłumaczony maszynowo, więc identyfikatory REST i Python należy zachować po angielsku.

## VS-008 — VisionStory API Overview2.pdf — 4 strony

**Weryfikacja duplikatu:** teksty s. 1–4 są 1:1 identyczne z wcześniejszym dokumentem VS-004 „VisionStory API Overview.pdf”. Pliki mają różne SHA-256, więc każdy dostaje własny ID źródłowy, ale nie tworzymy podwójnych wymagań.

| Strona | Treść | Ocena |
|---|---|---|
| 1 | Discover → submit → status → download; X-API-Key | Duplikat VS-004/1. Backend ma status i submission |
| 2 | API base HTTPS; data envelope, owned/public avatars i next_cursor | Duplikat VS-004/2. Paginacja awatarów dodana wcześniej |
| 3 | Publiczne i własne głosy, WAV/MP3 do SRT, koszt kreditów | Duplikat VS-004/3. STT i SRT nadal niewdrożone |
| 4 | vs_character_v4, brak 480p, 720p/1080p/2k, video beta, media understand | Duplikat VS-004/4. Tylko media understanding i odkrywanie modeli istnieją w adapterze |

## VS-009 — Talking Avatar Video API Quickstart — VisionStory.pdf — 7 stron

| Strona | Szczegóły instrukcji | Stan w kodzie |
|---|---|---|
| 1 | Pierwszy krok: prywatny klucz X-API-Key, nigdy publiczny frontend | Zgodne z backendowym VISIONSTORY_API_KEY |
| 2 | Weryfikacja klucza przez read-only billing/credits, następnie wybór SDK / CLI / MCP / Skill / REST | Odczyt salda w adapterze. CLI i Skill nie zainstalowano na urządzeniu właściciela |
| 3 | SDK Python oraz CLI installer, przejrzenie avatar/voice IDs, Agent Skill | Są endpointy odkrywania; konfiguracja mobilnego CLI/Skill niewdrożona |
| 4 | Agent Skill helper, POST video z model_id, avatar_id, client_request_id i text_script | Backend text/audio video + jawna zgoda na koszt działa jako kod |
| 5 | Żądania zwracają video_id, brak hardcoded IDs, rozłączność text_script/audio_script, polling co 5 s | Kod normalizuje status i zwraca sugestię polling; nie ma automatycznej trwałej kolejki |
| 6 | Failed => stop; timeout około 10 min; completed video_url; MP4 przechowywany 7 dni, należy go pobrać | **Dodano** bezpieczną archiwizację zakończonego MP4 i osobny uwierzytelniony endpoint pobrania; konfiguracja prywatnego magazynu jest obowiązkowa |
| 7 | Odnośniki do przewodników i schematów | Referencje; brak nowej implementacji |

Źródło sprawdzone dodatkowo: https://developers.visionstory.ai/guides/quick-start .

## Kod zrealizowany dla partii III

- GET /api/cinema/visionstory/voices?locale=en-GB&provider=minimax&limit=50&cursor=0 — wyszukiwanie głosów, BCP-47, dostawca i paginacja. Bez limitu zachowana poprzednia odpowiedź.
- GET /api/cinema/visionstory/ai-videos?status=queued,creating&limit=100&cursor=0 — odczyt listy zadań z filtrem i kursorem; nie rezerwuje dostępnego slotu i nie rozpoczyna generacji.
- POST /api/cinema/visionstory/talking-video/{video_id}/archive — sprawdza zakończenie filmu u VisionStory, pobiera MP4 wyłącznie z zatwierdzonego CDN, ogranicza ruch i zapisuje atomowo.
- GET /api/cinema/visionstory/talking-video/{video_id}/file — pobranie wyłącznie zapisanego już pliku, po autoryzacji gateway.
- Tests: tests/test_visionstory_batch03.py — wszystkie HTTP do providera, pobrania MP4 i DNS mockowane, brak kredytów użytych podczas testów.

## Archiwizacja MP4 — konfiguracja i ograniczenia

Na prywatnym backendzie należy ustawić:
- VISIONSTORY_MEDIA_DIR — absolutną ścieżkę trwałego wolumenu, np. /srv/unthinkable/visionstory.
- VISIONSTORY_MEDIA_ALLOWED_HOSTS — dokładne, zatwierdzone przez operatora domeny rzeczywistego CDN VisionStory; wildcardy nie są obsługiwane.
- Backend sprawdza publiczny adres IP rozwiązywanej domeny, pinning TLS, brak redirectów, MIME, podpis kontenera ftyp, limit 120 MiB i zapis atomowy.
- Brak powyższych ustawień oznacza odmowę pobierania. Nie używać przykładowych hostów w produkcji.
- Obecny gateway opiera się na jednym współdzielonym kluczu — **nie ma jeszcze produkcyjnej autoryzacji wielu tenantów do prywatnych plików**, więc użycie dla wielu niezaufanych użytkowników jest zablokowanym etapem.

## Nowe wymagania UI dla właściciela

| Podwidok | Co przygotować | Status |
|---|---|---|
| FILM-VS-VOICE-02 | Lista głosów, wybór regionu językowego BCP-47 i dostawcy, podgląd próbek, load-more | API istnieje; ekran Flutter brak |
| FILM-VS-JOBS-02 | Zadania generatywne queued / creating / created / failed, pagination, liczniki współbieżności | Read-only API istnieje; brak kompletnego UI i mechanizmu rezerwacji |
| FILM-VS-MP4-01 | Gotowe filmy: archiwizuj, stan zapisu, rozmiar, pobierz MP4, brak CDN/volumenu | API istnieje; ekran Flutter brak |
| FILM-VS-MODEL-02 | Zmiany wersji, 480p tylko historycznie, nowsze profile Seedream/GPT Image, ceny wg rozdzielczości | Projekt i research, silniki generacji brak |
| AUDIO-VS-STT-01 | Osobne SRT / diarization / word alignment, transkrypcja i eksport | Plan, backend STT brak |

**Luki pozostają:** faktyczny TTS/STT/SRT, złożony NLE, render Seedance/Wan/Kling, ceny przed wywołaniem, pełen MCP/Skill, trwały job store, Flutter podpięty do VisionStory, RBAC/tenancy, live provider account. Nie oznaczać ich jako DONE.

Następny dokument rejestrować jako VS-010.
