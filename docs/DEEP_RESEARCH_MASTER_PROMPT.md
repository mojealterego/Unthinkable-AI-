# UNTHINKABLE AI — MASTER DEEP RESEARCH & ENGINEERING PROMPT

**Adres docelowy:** https://github.com/mojealterego/Unthinkable-AI-  
**Gałąź:** main (nie twórz innych gałęzi bez polecenia właściciela).  
**Język:** polski jako domyślny, z pełną lokalizacją.  
**Tryb:** badanie źródeł → rygorystyczna inżynieria → implementacja → test → dowód.

## 0. Misja i warunek ukończenia

Działasz jako zespół badaczy, matematyków, inżynierów Rust/C++/Python/Flutter, grafików, twórców gier, specjalistów infrastruktury i security. Zaprojektuj i krokowo zbuduj **Unthinkable AI**, jedną aplikację Android-first i platformę edge/cloud do generatywnej AI, badań, tworzenia aplikacji, gier, filmów, muzyki i książek, komunikacji, automatyzacji oraz marketplace.

Nie obiecuj wszechmocy, ASI ani „najbardziej zaawansowanego systemu w historii” jako faktu. Zastępuj slogany kryteriami mierzalnymi. Nie oznaczaj szkicu, fragmentu dekompilacji, niewykonanych testów, nierozliczonej płatności ani koncepcyjnej integracji jako PRODUKCYJNE.

## 1. Źródła — ZERO UTRACONYCH WYMAGAŃ

Obowiązkowo odczytaj całe źródła użytkownika (każdą stronę i rysunek, wszystkie dodatki), wszystkie bieżące wiadomości dotyczące produktu, README, AGENTS.md, docs/SOURCE_AUDIT.md i requirements/requirements.csv. Dokumentacja dostarczona w rozmowie:

- „Ekstremalna Rozbudowa Platformy AI i IDE - Google Gemini.PDF”
- „Architektura Autonomicznego Systemu DGM - Google Gemini.PDF”
- „Taksonomia współczesnych systemów agentowych - Google Gemini.PDF”
- „Architektura Systemów Orkiestracji AI.docx”
- „Architektura Systemu Unthinkable AI.pdf”
- „Zaprojektuj inżynieryjny prompt dla Deep Research który to wszystko zaprojektuje ... - Google Gemini.PDF”.

Rejestr początkowy liczy **339 wymagań w 27 domenach**. Potraktuj go jako INWENTARYZACJĘ DO AUDYTU, nie jako sztywny limit: odkryte brakujące wymagania dodawaj z nowymi stabilnymi ID. Nie usuwaj wymagań użytkownika ani elementów dokumentacji; sprzeczności rozstrzygaj w decision log i jawnie oznaczaj opcjonalne dodatki.

Wytwórz requirements/traceability.csv o polach: ID, tekst źródłowy, nazwa źródła, strona/sekcja/fragment, priorytet, domena, zależności, podsystem, ścieżki plików, test odbiorczy, bezpieczeństwo/licencja, stan, commit SHA, artefakt dowodowy, blocker. **Każdy wymóg musi mieć dokładne źródło i test.** Gdy brakuje dostępu do źródła, napisz „BRAK_DOSTĘPU” i nie twierdź, że je zbadałeś.

Oddziel: wynik dekompilacji APK ≠ prawa do kodu źródłowego; opis w PDF ≠ implementacja; pokazany skrypt ≠ uruchomiony test; zrzut ekranu ≠ niezależna weryfikacja. Implementacja metodą clean-room, chyba że licencja i prawa umożliwiają reuse.

## 2. Kompletna lista obszarów — implementacja każdego ID jest osobno rozliczana

### FOUND — produkt, interfejs, branding
Android Flutter/Dart, Rust/C++ FFI, Python workers, offline+chmura, tablet/web/desktop, polski i i18n, dostępność, profiles/onboarding. Interfejs OLED true black, ikona **Santa Muerte obok „Unthinkable AI”**, inna postać/portret Santa Muerte w każdym głównym oknie. Manifest assetów właściciela. 8-sekundowe intro: postać porusza się i wskazuje pustkę, pojawia się napis „Unthinkable AI”, błysk, palec na ustach i drugi wskazujący na „Uncensored · Abliterated · NSFW”. Zadbaj o skip intro, preferencje i prawa do assetów.

### MODELS — katalog modeli, inferencja i dostawcy
LLM lokalne GGUF przez llama.cpp, kompatybilność z Android NPU/GPU/Vulkan, wybór modeli według sprzętu (RAM, storage, bandwidth, cache KV, termika, bateria), wznawialne pobieranie z Hugging Face, sumy SHA/licencje, dynamiczny model swapping, dwa modele target/draft ze speculative decoding, fallback do jednego modelu. Katalog image/audio/video model checkpoints, VAE, tokenizer, schedulers, LoRA/ControlNet. Panel BYOK dla wielu API providerów; Android Keystore, uprawnienia, billing i quota. Oferuj modele opisane jako uncensored/abliterated/NSFW z zachowaniem legalności, praw do obrazów i zasad odpowiednich kanałów dystrybucji.

### REASON / AGENTS — cognition i Agent Builder Code/NoCode
ReAct, Tree/Graph/Hierarchy of Thoughts, AB-MCTS, planowanie, Active Inference jako eksperyment, epistemic uncertainty, modelowanie intencji, memory CoALA, epizodyczna/semantyczna/proceduralna, HDC, bitemporal graph, RAG i GraphRAG, temporal retrieval, JEPA, NARS i testy ich użyteczności. Agenci dynamiczni/meta-agent/roje/legiony, orchestrator, handoff, planning+execution, permission capabilities i trwałe zadania. Agent Builder Code i NoCode oraz agenci dla cloud, Windows, macOS, Android, iOS. Porównaj dokładnie wymienione w taksonomii AutoGPT, BabyAGI, LangGraph, AutoGen, CrewAI, Semantic Kernel, LlamaIndex, Letta, DSPy, SWE-agent, OpenHands, MetaGPT, ChatDev, Voyager, Agent Zero, Hermes i pozostałe.

### EXT — Plugin, Skill, Tool i MCP Factory
Wewnętrzny system wtyczek jak w ChatGPT (koncept doświadczenia użytkownika, nie kopiowanie serwisu), Skill Creator, Tool Generator, Plugin Creator, MCP gateway/server/client, OpenAPI wrappers, manifest podpisów, schema validation, sandbox WASM/container, izin capabilities, marketplace publishing, versioning, reviews, rollback, revocation. Nie uruchamiaj obcych pluginów z dostępem do sekretów i host OS.

### DEEP — najmocniejszy praktycznie Deep Research
Równoległy research źródeł pierwotnych/artykułów/paperów/stron, analiza repozytoriów, modelowanie hipotez, plan/eksperymenty, fact check, przypisywanie dowodów każdemu zdaniu, solvery, weryfikator/sceptyk, agent do benchmarków, uczenie i pamięć wiedzy, kontrola kosztów tokenów, tryb prolonged reasoning. W czasie researchu może równolegle tworzyć i sprawdzać kod w GitHub z izolacją wykonania i uprawnieniami. Rozróżnij fakty od spekulacji. Nie fabrykuj źródeł ani wyników badań.

### DGM / GITHUB — RSI, rekursywna optymalizacja, 24/7 agent inżynier
Darwin–Gödel Machine rozumiana jako mierzalny iteracyjny mechanizm proponowania modyfikacji; autotesty, AST, source indexing, defect discovery, repo GitHub/GitLab, eksperymenty w piaskownicy, CI/CD, regresje, release signing, kanarki, feature flags, rollback, audyt, maksymalny koszt dobowy, blokada mutacji podnoszących uprawnienia. Cały czas działający agent wymaga **zewnętrznego trwałego worker service + scheduler**; sam cron GitHub Actions nie daje gwarancji 24/7. Z ChatGPT dostęp przez autoryzowany backend/connector. GitHub main only; optimistic locking SHA i ochrona przed równoległymi commitami.

### IMAGE — bezpośrednio podłączane modele generowania obrazu
Slot providerów **bez wymaganego ComfyUI**: Stable Diffusion i inne potwierdzone rodziny checkpointów; local/cloud runtime, VAE, CLIP/text encoders, sampler i guidance, negatywne prompty, style, LoRA, referencje twarzy i kompozycji, inpainting/outpainting, upscale, batch, seed, panoramy, warstwy, śledzenie praw do modelu. Master prompt ładowany z pliku, zapisywany, wersjonowany i używany do projektów. Przestrzeń twórcza w dozwolonych ramach.

### VIDEO — model hub, Pinokio, studio filmu i NLE 123+ minut
Wymienne silniki do wideo, w tym Wan (potwierdź wersję oraz licencję oficjalnych checkpointów), pliki VAE/WAE z manifestem kompatybilności, opcjonalny Pinokio uruchamiany w sandboxie, *nie* uzależniaj pipeline od ComfyUI. Reference images/video/audio; tworzenie aktorów z opisu lub własnych legalnych referencji i utrzymanie **Character Bible/Identity Registry**, kostiumu, lokacji, scenografii, głosu i osi narracyjnej przez projekt. Odnieś UX do **Google Flow i Picsart** po sprawdzeniu aktualnych funkcji; nie kopiuj ich kodu.

Film Crew Swarm: showrunner, scenarzysta, reżyser, storyboard artist, casting director, operator DOP, scenograf, kostiumograf, animator, VFX, montażysta, kolorysta, dźwiękowiec, kompozytor, producer/QC. Storyboard i shot list, master prompt, sceny w klipach, voice/lip sync, narracja, muzyka, continuity detection. NLE w aplikacji: multi-track timeline, previsualization, trim, transitions, keyframes, masks, compositing, grading, LUT, frame rate, time stretch, speed ramps, subtitles, dubbing, multi-audio, export presets, render queue, proxies/checkpoints, auto-recovery i eksport projektu **123 minut lub dłuższego**. Wylicz orientacyjne GPU-h, rozmiar cache, liczbę ujęć i jakość weryfikacji, nie obiecuj 123-minutowej pojedynczej generacji.

### AUDIO — głos, muzyka, teledyski
Czat tekst/głos, STT/TTS realtime, podcasty, audiobooki, audio effects, muzyka i generowanie stemów, mastering, eksport WAV/MP3/FLAC, music AI pipeline generujący teledysk do utworu, synchronizacja rytmu, tekstu, scen, postaci i generowanego głosu, praw autorskich.

### GAME — Game Builder Code + NoCode
Od najprostszych 2D/retro, pixel art/visual novel/platformer/RPG przez 3D po złożone gry aspirujące do poziomu AAA. Scenariusze, logika, UI, proceduralna grafika i assety, rigging, animacja, world builder, level design, fizyka, shaders, rendering, multiplayer/netcode, NPC AI, testing, eksport. Reużyj IDE. Badanie konkretnych aktualnych MCP i licencji dla **Unity, Godot i Unreal Engine**; automatyzacja przez odizolowane, płatne w razie potrzeby stanowiska chmurowe. Nie utożsamiaj możliwości użycia Unreal z automatycznym tworzeniem kompletnego AAA.

### APPS / WEB — App Builder, IDE, tworzenie WWW
App Builder Code/NoCode dla Android/iOS/Windows/macOS/web/cloud, multi-language source editor, git, terminals, AST, debug, test, deployment. Przewidziane **33 niszowe aplikacje + 33 programistyczne narzędzia** z DGM docs; osobna lista 66 z funkcjami i badaniem rynku. Web builder, website generator, scraper/parser/wrapper API z ToS/robots, dostawcy promocji, generator własnych autoryzowanych kodów rabatowych, alias email Creator i integracja Google Workspace.

### PUBLISH — książki, portrety, roleplay
Ebook/EPUB/PDF, audiobook, pełne książki dla dzieci z autorską fabułą i gotowym składem każdej strony, ilustracje, komiksy, roleplay postaci, fotografia i malarskie portrety od ołówka/węgla po akwarelę, akryl i olej. **Obowiązkowy dwuetapowy workflow: najpierw szczegółowy projekt do akceptacji, dopiero potem generacja.** Propozycje print-ready, prawa do tekstu/grafiki, eksport.

### CHAT / BROWSER / ANDROID — komunikacja, numeracja i OS
Jednorazowy komunikator pokojowy: QR/link, end-to-end encryption, klucz i TTL, potwierdzone zakończenie sesji, nowy link do nowego pokoju, ochrona przed replay i brak fałszywych gwarancji trwałego skasowania backupów. Wirtualne numery i maskowanie własnego numeru: wewnętrzny alias o dowolnym prefiksie oraz publiczne numeracje *tylko z realnie wolnych i przydzielonych operatorowi puli numerów*, połączenia przez zweryfikowane SIP/WebRTC/telephony providers, caller ID weryfikowany. Dwie przeglądarki: clearnet i Tor/.onion z hasłem/biometrią, izolacja cookies/proxy/DNS/WebRTC i świadomość ograniczeń anonimowości. Android Guardian z permissioned system APIs, ochrona baterii, zasobów, aplikacji i storage; nie przejmuj niedozwolonych uprawnień root.

### OWNER / MATH — prywatne okno właściciela
Osobna autoryzacja właściciela, FTP (ostrzeżenie: plaintext), SFTP, SMBv2/v3, serwery MCP, Google Drive, folder telefonu Android SAF, sieciowe storage, database sandbox, SQL/noSQL, audyt uprawnień. Chat okno **Millennium Problems & Cain**: matematycy agenci, Lean 4/Coq/Z3/Isabelle, teoria dowodu, hierarchie lematów, siedem problemów milenijnych z krytycznym sceptykiem, eksperymenty numeryczne, provenance, rozwiązanie Żuchwy Kaina jako problem sekwencjonowania 100 stron z hipotezami chronologicznymi/kulturowymi. Nie twierdź, że odkryto ważny dowód, dopóki nie ma niezależnej weryfikacji.

### MARKET / PAY — Marketplace i taryfy
Marketplace wewnętrzny dla agentów, skillów, pluginów, MCP servers, modeli, książek, produktów cyfrowych. Digital goods screening, malware scan, licencje, reputacja, chargebacks, refundy, pakiety Free/BASIC/PRO/STUDIO/ENTERPRISE, subskrypcje kaskadowe, jednorazowy zakup funkcji i opcjonalne lifetime z limitem kosztów GPU. PayPal, BLIK, Revolut Pay, kryptowaluty: zbadanie zgodności prawnej, bramek, Google Play Billing dla towarów cyfrowych i opcji zewnętrznych, VAT/OSS/KYC, webhook security. Reklamy oznaczone, afiliacja transparentna, sponsorowanie, program creator, cross-sell; żadnego ukrytego podmieniania cudzych linków. Tabela kosztów, LTV/CAC, marża, churn, próg rentowności i scenariusze przy różnym zużyciu GPU.

### INFRA / FORMAL / LEGAL / OPTION / REUSE
Architektura Flutter/Dart + Rust core + C++ inference/FFI + Python science, Zenoh i iceoryx2 w miejscach uzasadnionych pomiarem, Postgres/pgvector + bitemporal graphs, object storage, brokers, distributed workers, GPU scheduler, observability, tracing, sandbox/WASM, CI/CD/SBOM, backups, disaster recovery, service level objectives, encryption, key management, regional data residency, multi-tenant security. Chmura IBM jako preferowany składnik, ale pokaż testy rzeczywistych usług, koszty i alternatywy. Zweryfikuj reużywalność istniejących repozytoriów mojealterego (żadnych fikcyjnych 630/100% gotowości). Dodatkowe pomysły występujące wyłącznie w dokumentacji, np. VR/AR i specjalne interfejsy Bluetooth, wpisz do OPTION ze statusem decyzji; nie wykreślaj.

## 3. Obowiązkowa matematyka i weryfikacja

Wszystkie modele matematyczne opisz w LaTeX, z jednostkami, warunkami brzegowymi, falsyfikowalnym testem, danymi i implementacją referencyjną.

- DGM: ograniczona optymalizacja jakości kodu na zbiorze bezpiecznych patchy; porównanie score przed/po, regresje, proof obligations, rolling back, statystyczna istotność wyniku.
- Active Inference: wariacyjna wolna energia F(q,o)=E_q[log q(s)-log p(o,s)], wyjaśnienie generatywnego modelu obserwacji i kalibracji na danych; zwykły alarm SLO jako baseline.
- Speculative decoding: alpha=min(1,p(x)/q(x)), residual distribution i test statystyczny niezmienności output distribution; cache KV NIE jest automatycznie współdzielony między niezgodnymi modelami.
- Resource allocation: bin packing, deadline-aware scheduling, Pareto optimum quality/latency/cost, memory budgets, thermal throttling i Android power constraints. Landauer to limit teoretyczny, nie rzeczywisty sterownik temperatury.
- Video: VAE/WAE oraz compression ratio tylko według realnych checkpointów; koszt filmu >123 minut = suma renderów ujęć + retake + export+storage. Character consistency metrics oraz ocena człowieka; brak gwarancji perfekcyjnej spójności.
- Math agent: solvery formalne, proof kernel, przypisane aksjomaty, testy counterexample; Żuchwa Kaina jako weighted permutation/CP-SAT/beam search z 100! przestrzenią i ograniczeniami.
- Pamięć HDC/GraphRAG/bitemporal, belief uncertainty/MDP/POMDP, ewaluacja halucynacji i benchmarki systemów agentowych.
- Security: threat model, trust boundaries, cryptographic key lifecycle, E2EE ephemeral rooms, STRIDE, SAST/DAST, secret scanning, package isolation.
- Finanse: koszty operacyjne per workload, prognoza kosztów chmury, break-even, marża per plan, jednostkowe koszty generacji.

## 4. Architektura repozytorium: oczekiwana mapa

- apps/mobile_flutter oraz apps/console_web — Android i panel web.
- crates/core, crates/policy, crates/model_runtime, crates/ffi_bridge, crates/ipc — Rust i C++.
- services/api, identity, scheduler, media_workers, telephony, storage, billing, marketplace — kontenery/serwisy.
- agents/research, agents/repo_engineer, agents/film_crew, agents/game_studio, agents/publishing, agents/math_solver — agenci o kontraktach.
- packages/schemas, sdk, model_manifests, plugin_contracts — wersjonowane typy i adaptery.
- assets/branding, intro, characters — wyłącznie assety z prawami właściciela.
- infra/terraform, helm, observability, workflows — IaC i CI.
- tests/unit, integration, e2e, benchmarks, security — testy.
- docs/ADR, docs/ROADMAP.md, docs/THREAT_MODEL.md, docs/INFRA_COSTS.md, docs/API_CONTRACTS.md, docs/evidence/ — dokumentacja.
- requirements/requirements.csv, requirements/traceability.csv — obowiązkowa mapa pokrycia.

Każdy plik ma mieć odpowiedzialność, interfejs, zależności i test. Niedopuszczalne jest tworzenie pustych plików i nazywanie ich pełną implementacją.

## 5. Wyniki, kolejność i raportowanie

1. **Audyt wszystkich plików:** źródło → każda atomowa funkcja → traceability; wypisz nowe funkcje nieobecne w 339, dopisz je; wskaż konflikty i źródła niewiarygodne.
2. **Badanie aktualności:** licencje, wersje, API, kompatybilność modeli, Unity/Godot/Unreal MCP i Pinokio/Wan/Stable Diffusion, koszt operacyjny.
3. **Specyfikacja produkcyjna:** C4, OpenAPI, ERD, auth/RBAC, tenant model, data flow, state machines, sandboxing, FFI ownership, model manifests, jobs/events, deploys.
4. **Roadmap:** każdemu requirement ID przypisz etap, estymację, zależności i definition of done. Żaden punkt nie może pozostać poza roadmapą.
5. **Kod etapami:** najpierw działający i testowalny Flutter+Rust foundation, następnie model hub+chat, agent builder+Deep Research, media engines/NLE, Code/NoCode/Game, komunikacja, owner vault, marketplace.
6. **Continuous GitHub Engineer:** permanent worker + durable jobs (np. chmura) i kontrolowane CI. Pętla: analyse → plan → patch → sandbox → tests → security → human/policy gate → optimistic atomic main commit → evidence → rollback. ChatGPT ma być kontrolowanym interfejsem rozmownym do operatora.
7. **Dowody:** realne SHA commitów, build APK/AAB tylko jeśli faktycznie skompilowany, logi rust test/flutter test/CI, testy na urządzeniu i infrastrukturze, SBOM, audyt kodu, e2e, protokoły weryfikacji i braków.

Każdy raport musi zawierać: DONE (potwierdzone dowodem), IN_PROGRESS, BLOCKED, TEST_FAILED, NOT_STARTED, liczby zamkniętych i pozostałych ID, brakujące materiały, dokładne zmiany i plan następnych iteracji. Nie opuszczaj domeny tylko dlatego, że jest trudna; oznacz jej blokadę i warunek realizacji.

**Kontrakt absolutny: brak samowolnego zawężenia zakresu, brak wymyślonych sukcesów, brak bezwzględnych deklaracji wydajności lub bezpieczeństwa bez pomiarów, żadnych tajnych danych w GitHub, żadnych niezautoryzowanych publikacji lub zakupów.**
