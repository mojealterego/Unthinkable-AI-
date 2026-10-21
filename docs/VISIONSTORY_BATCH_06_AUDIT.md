# VisionStory — partia VI: VS-016 / VS-017

**Data:** 21.10.2026. Przyjęto 3 pliki, 15 stron fizycznych; jeden jest już zarejestrowany jako VS-010 (identyczny hash). Nowych jest 2 PDF-y / 10 stron. Po uzupełnieniu rejestru: 17 odrębnych plików / 108 stron. Następny identyfikator: VS-018.

| Plik | Status | SHA-256 |
|---|---|---|
| AI Avatar API — VisionStory.pdf, 5 s. | Powtórka VS-010; nie nadawać nowego ID | 959fc5edb4134c3864d15c3e46b040bd2263930ba22a9be7b55fdd87c31f5e2a |
| AI Avatar API — VisionStory(1).PDF, 5 s. | Nowy VS-016; angielski odpowiednik | 4f5fd99355495eb8bcacd3fa4e0b1a9387cb1bdf55de9f0e193fdc27358525c6 |
| AI Image Generation API — VisionStory.PDF, 5 s. | Nowy VS-017; odrębny zakres obrazów | ad7c5502625910dbaa0b284b9268477729a0d81e658220f0fa3c106cd7ab56d5 |

## VS-016: AI Avatar API — VisionStory (1), 5 stron

| Strona | Dokładny zakres | Wynik / luka |
|---:|---|---|
| 1 | GET /api/v1/avatars, POST /api/v1/avatar, POST /api/v1/avatar/framing, DELETE /api/v1/avatar | Własne/publiczne awatary, tworzenie i kadrowanie w backendzie istnieją. Automatycznego DELETE brak; nie uruchamiać operacji destrukcyjnej bez potwierdzenia |
| 2 | is_public, limit 1–100, cursor, next_cursor=0; owned ma trzy framingi i default_voice_id, public framing=null | Backend paginacji istnieje; UI galerii i podgląd wszystkich kadrów jest częściowy |
| 3 | Portret HTTPS URL albo inline base64; JPEG, PNG, WebP, HEIC; max 10 MB; zwrot avatar_id | Tworzenie, potwierdzenie praw i zgody osoby w backendzie. Picker Flutter ogranicza do 8 MB — do rozbudowania o zgodny upload do 10 MB |
| 4 | avatar_id, aspect_ratio 9:16/16:9/1:1, zoom>=1, offset_x/y od -1 do 1; framing_unavailable i max_zoom dla złego obrazu | Zastąpiono stałe (zoom=1,x=0,y=0) edytowalnymi parametrami i osobnym wyborem proporcji. Nadal do dopracowania preview i komunikaty max_zoom |
| 5 | Wideo używa avatar_id oraz text_script.voice_id; usunięcie nie usuwa istniejących filmów | Powiązanie z talking-video istnieje. DELETE nadal tylko po jednostkowym, rzeczywistym zatwierdzeniu |

VS-010 i VS-016 opisują te same wymagania merytoryczne w polskim tłumaczeniu i angielskim oryginale. Nie dublować implementacji.

## VS-017: AI Image Generation API — VisionStory, 5 stron

| Strona | Zawartość dokumentu | Wynik / luka |
|---:|---|---|
| 1 | Beta Pro+, GET /api/v1/image/models, POST /api/v1/image; edycja obrazów przez prompt i referencje | Backend obu operacji istniał, ale konto Pro+ niezweryfikowane |
| 2 | Siedem modeli: Nano Banana 2/Pro, Seedream 5 Lite/Pro, GPT Image 2.5 Flare/Sunburst i GPT Image 2; max prompt 3000/5000 znaków, refs 4/6/10/14; ceny credit_by_resolution | Dodano bezpłatną wycenę POST /api/cinema/visionstory/images/estimate. Kwotę i limity wyznacza bieżący katalog; nie kodować modeli/cen na stałe |
| 3 | 10 proporcji, rozdzielczość zależna od modelu (np. Seedream Lite 2K/4K, Pro 1K/2K); brak publicznego quality; instrukcyjne edytowanie przez refs, URL obrazu w odpowiedzi | Dodano w Flutterze wybór rozdzielczości/proporcji z katalogu oraz podgląd kosztu. Nie dodawać nieistniejącego quality |
| 4 | Dla GPT Image timeout minimum 180 s i brak automatycznych retry; URL obrazu można przenieść do generowania klipu (first_frame/refs); obraz nie jest zapisywany jako własny asset | Naprawiono 20→190 s po stronie REST, przed płatnym POST zapisywany lokalnie stan żądania w Flutter. Brak automatycznej trwałej biblioteki obrazów i bezpośredniego podpięcia do storyboardu |
| 5 | Cena tylko za sukces, błędy 37100/37101, limit współbieżności beta; koszty 1K/2K mogą różnić się | Backend ponownie weryfikuje realną cenę i saldo przed POST; testy mockowane. Brak wieloużytkownikowego limitu równoległych kosztów |

## Zmiany kodu i testy

- services/visionstory/client.py — timeout 190 s dla płatnych synchronicznych obrazów.
- services/visionstory/media_tools.py — cena z live model params, obsługa różnych rozdzielczości, read-only estimate, jawny limit kredytów.
- lib/features/video/visionstory_media_tools_screen.dart — selektory opcji modelu, wycena bez renderowania, potwierdzenie kosztów, restart-safe blokada przypadkowej drugiej generacji, trzy edytowalne parametry framing.
- tests/test_visionstory_media_tools.py — testy model limit/price, brak płatnego POST przy estimate, 190 s transportu.

## Stan projektu: nieukończone z wcześniejszych VS-001–VS-017

Do faktycznego ukończenia pozostały: produkcyjne konto i dostęp VisionStory Pro+; różne klucze i ACL tenantów; host i pełny MCP/Skill; trwała baza assetów z automatycznym eksportem do NLE; duże uploady 10/30/100 MB; podgląd awatara i obrazu; prawdziwy wielościeżkowy NLE z ciągłością aktorów i filmem 123+ minut; integracja MP3→teledysk; test płatnych modeli na koncie operatora po zgodzie; finalny autorski design i testy na urządzeniach.

**Wniosek:** prototypowe endpointy i testy mock nie są dowodem pełnego wykonania VisionStory ani całego Unthinkable AI. Nie przyjmować kolejnych materiałów jako powodu do zamknięcia powyższych zaległości.
