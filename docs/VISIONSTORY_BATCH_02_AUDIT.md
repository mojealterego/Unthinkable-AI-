# VisionStory — II partia: PDF 4–6 z co najmniej 66 materiałów

Data rejestracji: 2026-10-19. Właściciel zapowiedział **co najmniej 60 dodatkowych plików**. Rejestr obejmuje **sześć otrzymanych PDF-ów, 34 strony**, z czego aktualna partia zawiera **trzy PDF-y i 14 stron**. Pozostałych 60+ materiałów jeszcze nie otrzymano ani nie analizowano. Aktualizacja jest **przyrostowa**; nie zamyka zakresu Studia Filmowego.

Weryfikowalne nazwy, liczbę stron oraz SHA-256 przechowuje `requirements/visionstory_sources.csv`. Numeracja VS-001..VS-006 jest trwała; kolejne pliki dodawać jako VS-007 itd. Ten rejestr nie zawiera kopii chronionych prawem PDF-ów.

## Strona po stronie: VS-004 — VisionStory API Overview.pdf (4 strony)

| Strona | Informacje źródłowe | Konsekwencja dla Unthinkable AI |
|---|---|---|
| 1 | REST API, workflow discover → POST video → GET status → download; również awatary, głosy, transkrypcje, obrazy i wideo | Ten sam provider i wspólna kolejka; istniejący adapter pokrywa tekst/audio talking-avatar częściowo |
| 2 | `https://openapi.visionstory.ai`, `X-API-Key`, koperta `data`; własne i publiczne awatary, `is_public=true`, `next_cursor` | Wymagane: paginacja `cursor` i `next_cursor` dla list awatarów; kod jeszcze bez paginacji |
| 3 | Głosy publiczne i własne; WAV/MP3 transkrypcja z timestampami, speaker labels, SRT; kredyty za generację, zwrot przy niepowodzeniu według dostawcy, `cost_credit` przy statusie | Wymagane: Studio Napisy + Audio Alignment, monitor kosztu/zwrotów. Zwrot kredytów to deklaracja dostawcy, nie dowód z konta |
| 4 | `vs_character_v4`, 720p/1080p/2k, 9:16/16:9/1:1, max 600 s; `vs_talk_v1` wycofany, 480p niedozwolone; wideo AI beta; `POST /api/v1/media/understand` JSON dla 1–8 mediów | Nie eksponować wycofanego modelu, nie dodawać 480p. Dodać formalne Studio „Analizuj media”, ale bez generowania fałszywego endpointu |

## Strona po stronie: VS-005 — VisionStory API Reference.pdf (2 strony)

| Strona | Informacje źródłowe | Konsekwencja |
|---|---|---|
| 1 | Jeden bazowy REST endpoint i `X-API-Key`; katalog REST obejmuje video/avatar/voice/TTS/image/AI video/assets; SDK, CLI, MCP, Skill, `llms.txt`, OpenAPI JSON | Nie deklarować, że obecny adapter 11 endpointów obejmuje pełen interfejs dostawcy |
| 2 | Odsyłacz do pełnej dokumentacji endpointów, schematów, błędów i przykładów | Ten PDF jest indeksem, **nie** pełną specyfikacją 28 operacji; parametry nieobecne tutaj muszą pochodzić z `openapi.json` i dalszych PDF |

## Strona po stronie: VS-006 — VisionStory API for AI Agents.pdf (8 stron)

| Strona | Informacje źródłowe | Konsekwencja |
|---|---|---|
| 1 | MCP, Agent Skill, Python SDK, CLI; wszystkie używają tego samego REST i `VISIONSTORY_API_KEY` | Znormalizowany adapter narzędzi `ProviderCapabilities`; nie instalować zależności automatycznie |
| 2 | Agent Skill, `llms.txt`; klucz lokalnie; kontrola kredytów przed płatnym zadaniem; **28 operacji MCP/SDK/CLI** | Osobny profil uprawnień agenta, rozdział odczyt i opłacane operacje, rejestr 28 operacji dopiero po enumeracji OpenAPI |
| 3 | Local `uvx visionstory-mcp`, health check; alternatywnie `pip install visionstory-mcp`; MCP environment | Konfigurator „MCP lokalny” + stan połączenia. W polskim PDF nazwy poleceń i kluczy zostały automatycznie przetłumaczone — implementacja ma zachować oryginalne nazwy |
| 4 | Zdalny Streamable HTTP `/mcp`, nie posiada plików lokalnych; kontrola aktualizacji (`VISIONSTORY_UPDATE_CHECK=0`), usuwanie tylko po potwierdzeniu | Konfigurator „MCP zdalny”, upload plików użytkownika z wyraźną zgodą, safe secret vault, wersja/upgrade status |
| 5 | SDK, własne awatary/public avatars, voice listing, CLI, instalacja GitHub Agent Skill | Ekrany repo adapterów, katalog awatarów i głosów; walidacja źródeł i praw dostępu |
| 6 | Skill ma instrukcje i pomocniczy skrypt, ale **nie pokrywa wszystkich 28 operacji**; ewentualny alert Snyk W011 wymaga analizy; `llms.txt` i `.md` dokumentacji | Nie oznaczać Skills jako pełnego MCP. Audyt łańcucha dostaw i uprawnionych wyjść sieciowych przed instalacją |
| 7 | `llms-full.txt`, `openapi.json`, natural language agent tasks, klucz nigdy w logach; rzeczywiste ID discovery; idempotencja; polling ≥5 s, limit 10 min | Wymagany engine narzędzi: discovery → read-only budget → approval → submit → poll → download; nie wywoływać delete |
| 8 | Audio/video transcript + subtitle align, `understand_media` 1–8 referencji i schemat JSON obiektu; prompt 1–5000 znaków, synchronicznie do 180 s, koszty, bez automatycznego retry po timeout | Nowe zadanie „Analiza treści mediów” oraz transkrypcja z SRT; UI kosztu i ostrzeżenia o timeout; backend **nie jest jeszcze zaimplementowany** |

## Ustalony rejestr luk / priorytet implementacji

| Wymaganie | Kod w main | Brak / następny etap |
|---|---|---|
| REST key `X-API-Key`, API models/voices/avatars/credits | Backend istnieje i był testowany mockami | Wdrożony tenant vault i test live readonly |
| Awatar z tekstu lub MP3, emotion/chromakey/denoise | Backend istnieje, mock CI | Flutter UX + integracja konta użytkownika i zapis MP4 |
| Publiczne awatary i owned avatars | Backend read-only istnieje | Paginacja `next_cursor`, wyszukiwanie, cache, bez utraty praw własności |
| Voice transcription, SRT, diarization, word alignment | BRAK | SDK/API typed adapter dopiero po sprawdzeniu schematu |
| `POST /api/v1/media/understand` | BRAK | Walidator prompt/schema/referencji, koszt, blokada automatycznego retry; dopiero po kontrakcie API |
| MCP local + remote /28 provider operations | BRAK uruchomionego serwera i pełnego katalogu | Capability-based integration, full operation inventory, brak sekretów w aplikacji |
| Agent Skill na GitHub / plugin registry | BRAK integracji | Przegląd źródeł/licencji i Supply Chain/Snyk, dopiero potem instalacja |
| Film generatywny, NLE 123+, MP3→teledysk | Nieukończone | Autoryzowane API jobs, storage, segmentacja/montaż |

**Uwaga o źródłach:** są przetłumaczonymi kopiami stron; nazwy widoczne jako „Historia wizji”, „klucz X-API” czy „utwórz-wideo” nie są poprawnymi nazwami importów ani poleceń. Zachować realne `visionstory`, `X-API-Key`, `client_request_id`, `visionstory-mcp`, `openapi.json`. Bez dostępu do aktualnego OpenAPI i konta nie zgadywać pozostałych ścieżek/parametrów.

## Ekrany UI — *rozszerzenie* już istniejących, bez zamykania całej makiety

- `VIDEO-VS-AGENT-01` MCP Provider Connect: local/remote, status, uprawnienia, read-only.
- `VIDEO-VS-AGENT-02` Tools catalog: operacje read/write/paid/delete, źródła + licencja, dostępności.
- `VIDEO-VS-AGENT-03` Skill/SDK/CLI Setup: zatwierdzanie instalacji i alertów bezpieczeństwa.
- `VIDEO-VS-AGENT-04` Agent task builder: prompt, referencje, budget, preflight, koszty.
- `VIDEO-VS-MEDIA-01` Media understanding: 1–8 obrazów/audio/wideo, JSON schema, output JSON, billing.
- `VIDEO-VS-MEDIA-02` Speech Studio: STT/diarization, word timecodes, subtitles SRT/alignment.
- `VIDEO-VS-AVATAR-01` Avatar browser: owned/public, paginacja, kursory, ustawienia ramki.
- `VIDEO-VS-BILLING-01` Balance / costs / refund history and paid action approvals.

**Status wszystkich nowych widoków: do projektowania.** Nie zwiększać automatycznie sumarycznej liczby ekranów; częściowo pokrywają już istniejące VIDEO/AUDIO/EXT/AGENTS.

## Procedura dla pozostałych ≥60 plików

Dla każdego nowego pliku:
1. Nadać `VS-007` i kolejne, zapisać dosłowną nazwę, liczbę stron i SHA-256; nigdy nie zastępować wcześniej nadanego ID.
2. Przejść wszystkie strony, łącznie z tabelami/screenami, i zarejestrować wymogi przypisane do stron.
3. Sprawdzić unikalność, sprzeczności względem poprzednich dokumentów oraz możliwość ponownego użycia istniejącego kodu.
4. Rozdzielić implementację, testy i dowody CI od propozycji oraz funkcji wymagających płatnego dostępu.
5. Uzupełnić macierz UI; nie projektować grafik zamiast właściciela.
6. Dopiero po przeglądzie kompletnej partii ustalić ostateczną liczbę ekranów i listę integracji.


## Wdrożenie luk z partii II — 2026-10-19

- **VS-004 str. 2:** GET `/api/cinema/visionstory/avatars` oraz `/avatars/public` mają teraz `limit` (1–100) i `cursor` (liczba dodatnia). Dane i `next_cursor` pochodzą z upstream. Brak lokalnego serwisu cache/GUI Flutter.
- **VS-004 str. 4 i VS-006 str. 8:** POST `/api/cinema/visionstory/media/understand` wykonuje ustrukturyzowaną analizę mediów z backendu. Kontrakt producenta potwierdzony w jego dokumencie `https://developers.visionstory.ai/reference/media-understanding/understand-media`. Walidacja 1–8 mediów, schematu typu object ≤20 KB, base64, publicznego HTTPS i łącznego inline media ≤14MB; osobna zgoda na użycie mediów i płatną operację. Weryfikuje saldo kredytów. Zwraca `output`, `usage`, `cost_credit`, nie ponawia automatycznie po timeout.
- Testy `tests/test_visionstory_new_functions.py` wykorzystują fałszywego dostawcę — nie zużywają kredytów.
- **Nadal brak:** Flutter UI, połączenia z kontem producenta, SRT/diarization, lokalnego/remote MCP, pełnego przeglądu 28 operacji, trwałego magazynu zadań i realnego renderowania. To nie jest ukończona cała integracja.
