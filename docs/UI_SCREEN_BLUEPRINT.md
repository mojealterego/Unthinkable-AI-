# UNTHINKABLE AI — projektowanie UI: mapa ekranów

Status źródła: repo `mojealterego/Unthinkable-AI-`, `main`, 2026-10-19. Pełna lista **141 ekranów** (w tym 32 dla WWW) została przygotowana jako osobne pliki MD/CSV dla właściciela; poniższy wykaz repozytoryjny przechowuje podział, integracje i 32 ekrany WWW.

**Nie mylić projektu ekranu z implementacją.** `KOD` = obecny kod, niekoniecznie wdrożony publicznie; `CZĘŚĆ` = działający fragment, ale nie komplet funkcji; `PLAN` = jeszcze nie wdrożono.

## Moduły całej aplikacji

| Domena UI | Ekrany | Zakres |
|---|---:|---|
| CORE | 9 | branding Santa Muerte, intro, home, konto, pliki, zgody |
| MODEL | 10 | czat, BYOK, model hub, GGUF, VAE, Hugging Face, lokalna inferencja |
| IMAGE | 9 | obraz AI, inpainting, retusz, komiks, portrety, face swap |
| FILM | 14 | studio scen, ekipa 18 ról, model wideo, NLE 123+, eksport |
| AUDIO | 8 | muzyka, voice clone, TTS, extraction, podcast, teledysk |
| WEB | 32 | scraper, wrapper, NoCode, multi-page, import, hosting |
| PHONE | 12 | aliasy, VIP, rezerwacje on-net, DID, SIP/WebRTC, SMS |
| AGENT | 11 | agent/tool/skill/plugin/MCP builder, research, DGM/GitHub |
| APP | 8 | IDE, App Builder, Game Builder, Godot/Unity/Unreal |
| CHAT | 2 | komunikator, jednorazowe pokoje QR/E2EE |
| BROWSER | 2 | clearnet i zabezpieczony Tor/.onion |
| ANDROID | 1 | guardian systemu Android |
| PUBLISH | 5 | ebook, audiobook, roleplay, dziecięce książki, portret |
| OWNER | 4 | vault, SFTP, SMB, Drive, telefon, sandbox DB |
| MATH | 3 | Millennium Problems, Cain, formal proof |
| MARKET | 3 | marketplace, karta produktu, panel sprzedawcy |
| PAY | 4 | taryfy, checkout, faktury, afiliacja |
| ADMIN | 4 | cloud GPU, bezpieczeństwo, CI, utrzymanie |

Łącznie: **141 ekranów/widoków**. To mapa UX, nie 141 niezależnych implementacji. Zachować rejestry `requirements/requirements.csv` (339 IDs), `requirements/user-directives.psv` (146 directives), `requirements/source-candidates.psv` (53 kandydatów).

## Website Studio: wszystkie 32 ekrany szczegółowo

| ID | Ekran | Stan | Co musi pokazywać / z czym się łączy |
|---|---|---|---|
| 51 | Web Studio — wybór zadania | CZĘŚĆ | połączyć dwa istniejące UI WEB w jeden punkt wejścia |
| 52 | Moje strony i projekty WWW | CZĘŚĆ | wspólny zapis, import, eksport, wersje |
| 53 | Uprawnienia do skanowania | CZĘŚĆ | potwierdzenie własności domeny, allowlist, robots.txt |
| 54 | Web Scraper — URL i ustawienia | CZĘŚĆ | skan autoryzowanego HTTPS, limit stron, tryb HTML |
| 55 | Inspektor HTML/DOM | KOD | nagłówki, media, linki, formularze; bez skryptów i sekretów |
| 56 | Mapa struktury witryny | CZĘŚĆ | drzewo podstron i nawigacji; limitowany crawl |
| 57 | Capture SPA / DOM po JS | PLAN | Playwright/Puppeteer w izolowanym workerze |
| 58 | Zasoby strony / assety | PLAN | legalny import obrazów, fontów i CSS |
| 59 | Porównanie stron i audyt | PLAN | zrzuty, SEO, a11y, diff |
| 60 | Wrapper: snapshot witryny | CZĘŚĆ | mapowanie publicznych elementów do edytora |
| 61 | API Wrapper: edytor endpointów | KOD | operacje GET/POST/PUT/PATCH/DELETE |
| 62 | OpenAPI podgląd i eksport | KOD | kontrakt OpenAPI 3.1, JSON |
| 63 | API Test Console | PLAN | własne API i autoryzowany test połączeń |
| 64 | API credentials / OAuth | PLAN | bezpieczne uprawnienia do własnych serwisów |
| 65 | Generator SDK / wrappera | PLAN | typowany klient i autoryzowane adaptery |
| 66 | NoCode kreator projektu | CZĘŚĆ | tytuł, motyw, szablony |
| 67 | NoCode podstrony i nawigacja | KOD | edycja podstron i slugów |
| 68 | NoCode sekcje i bloki | KOD | hero, opis, korzyści, CTA, kontakt |
| 69 | NoCode drag-and-drop | PLAN | wizualny WYSIWYG i siatka |
| 70 | Motywy i presety designu | CZĘŚĆ | m.in. gold, dark, light |
| 71 | Biblioteka assetów WWW | PLAN | obrazy, ikony, typografia, upload |
| 72 | Formularze i dane | PLAN | działający backend formularzy |
| 73 | CMS i dynamiczne kolekcje | PLAN | blog, dane produktów, bazy |
| 74 | Responsive preview | CZĘŚĆ | podgląd mobilny i serwerowy HTML |
| 75 | SEO i dostępność | PLAN | audyt, accessibility, meta |
| 76 | Zapis i wersje projektu | CZĘŚĆ | local/JSON istnieje, historia i undo nie |
| 77 | Eksport HTML/CSS/ZIP/JSON | KOD | dwie implementacje eksportu |
| 78 | Publikacja i hosting | PLAN | połączenie z usługą, custom domain i HTTPS |
| 79 | Migracja własnego backendu | PLAN | SSH, import bazy i pliki tylko z uprawnieniami |
| 80 | Migracja DNS/SSL | PLAN | weryfikacja, deploy, rollback |
| 81 | Promocje i kupony | PLAN | własne kampanie i kod rabatowy |
| 82 | Alias e-mail Creator | PLAN | Google Workspace, zweryfikowana domena |

## Faktyczne backendy WWW

- `/api/web-studio`: inspektor HTML, restrykcyjny HTTPS scraper, manualne OpenAPI, jedno-stronicowe HTML/ZIP.
- `/api/web`: legalny limitowany scrape, ekstrakcja, wrapper snapshot, wielostronicowy NoCode, templates, preview, ZIP i import snapshotów.
- Flutter: `lib/features/web_studio` oraz `lib/features/web`. To dwie implementacje prototypowe do ujednolicenia UI — **nie dwa docelowe produkty**.
- Integracje z PDF (HTTrack, Wget, Puppeteer/Playwright, Cheerio, Burp/Postman, mitmproxy, SSH/Rsync, Docker/Terraform, mysqldump/pg_dump, worker threads) są częściowo **propozycjami technicznymi**, nie działającym modułem produkcyjnym.

## Reguły projektowania

1. Santa Muerte, branding, polski język, adaptacyjne ekrany, prawa do grafik. Materiały graficzne dostarcza właściciel.
2. Dla każdego ekranu: empty/loading/error/offline/no-permission/no-backend; w kreatorach: edycja → podgląd → akceptacja → eksport.
3. Nie sugerować, że fragmenty publicznego HTML zawierają backend, źródła serwera, sesje lub bazę danych.
4. Numery on-net nie są publicznymi DID, most natywny ODYN nie jest działającym silnikiem dyfuzji, kompilacja debug APK nie jest pełnym release.
5. Wspólne projekty/asset store/branding i jedno źródło statusu dla scraper, wrapper i NoCode.

## Priorytet dla projektanta

**P0:** globalna nawigacja, ekran `WEB 51`, `WEB 53–55`, `WEB 60–62`, `WEB 66–68`, `WEB 74`, `WEB 76–77`; aktualne moduły filmu, chat, model hub i Virtual Number.

**P1:** `WEB 56–59`, `63–65`, `69–73`, `75`, `78–80`; obrazy, wideo, audio, creatorów. **P2:** marketplace, płatności, zaawansowana autonomizacja i połączenia z infrastrukturą.

Stan funkcji musi pochodzić z rzeczywistych testów uruchomionych dla danego modułu, nie z wyglądu makiety.

## VisionStory AI — dwanaście podwidoków Studia Filmowego (2026-10-19)

VisionStory to zewnętrzny silnik REST; nie zastępuje ODYN ani NLE. Dwanaście pozycji F-VS-01..12 to podwidoki do projektu UI FILM, nie automatycznie dwanaście nowych ekranów głównych (bez analizy pokrycia poprzednich 141).

| ID | Podwidok UI | Stan | Integracje |
|---|---|---|---|
| F-VS-01 | VisionStory: konfiguracja | Backend | Dostęp do serwera, bez wyświetlania sekretu |
| F-VS-02 | Plan i kredyty | Backend | GET billing/credits, zgoda na koszt |
| F-VS-03 | Modele mówiących awatarów | Backend | GET models, ratio, rozdzielczości |
| F-VS-04 | Katalog awatarów | Backend | GET avatars, galeria publiczna/własna |
| F-VS-05 | Tworzenie awatara | Plan | Własny portret, kadrowanie, zgoda |
| F-VS-06 | Katalog głosów | Backend | GET voices, język, odsłuch |
| F-VS-07 | Klonowanie głosu | Plan | Próbka i zgoda właściciela |
| F-VS-08 | Awatar mówiący | Backend: tekst / Plan: audio | Scenariusz lub nagranie |
| F-VS-09 | Parametry i potwierdzenie renderowania | Backend | Ochrona kosztów, idempotencja |
| F-VS-10 | Kolejka i status wideo | Backend | Video ID, queued/creating/created/failed |
| F-VS-11 | Podgląd i pobranie MP4 | Plan po stronie Androida | Retencja 7 dni, archiwum projektu |
| F-VS-12 | Inne silniki VisionStory | Plan | AI video refs, obraz, TTS, STT, assety, MCP/Skill |

Backend: services/visionstory i /api/cinema/visionstory/*. Testy z mockowanym API, bez połączenia z kontem użytkownika. Brak potwierdzonego live video. Dokładny projekt graficzny pozostaje po stronie właściciela.
