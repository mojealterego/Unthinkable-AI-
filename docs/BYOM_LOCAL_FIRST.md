# Unthinkable AI — własny ekosystem BYOM (Owner Directive)

## Zasada architektoniczna

To **własna aplikacja i własne silniki**, a nie agregator zewnętrznych kont VisionStory. Dane referencyjne stron trzecich pomagają w analizie UX/funkcji, ale ich interfejsy API nie są domyślnym środowiskiem wykonywania. Nie kierować użytkownika do kont, kluczy i płatnych kredytów firm trzecich dla podstawowych funkcji.

**Model-first**: GGUF, safetensors; Standard/Uncensored/Abliterated jako metadane. Zadania: text, image, video, audio. Plik jest kopiowany do app-private storage i dostaje SHA-256. Sam import NIE oznacza działającego silnika. Właściciel określa licencję i uprawnienia do modelu. Nie zakładać technicznego bezpieczeństwa ani zgodności dowolnych wag z dowolnym silnikiem.

## Czat lokalny: wykonana ścieżka

- Domyślny serwer: \`http://127.0.0.1:8080/v1\` (np. uruchomiony oddzielnie \`llama.cpp llama-server\`).
- \`GET /v1/models\` wykrywa rzeczywiste ID, \`POST /v1/chat/completions\` rozmawia z wybranym modelem.
- Loopback HTTP ma **brak** klucza, zewnętrzne HTTPS wymaga klucza właściciela; nie wysyłać sekretów przez HTTP.
- Android config: \`tools/configure_android_local_runtime.py\` po \`flutter create\`, dodaje INTERNET i zezwala na cleartext wyłącznie localhost/127.0.0.1.
- Domyślnie brak zewnętrznego endpointu. API provider jest opcjonalnym adapterem, a nie kontem aplikacji.

**Weryfikacja:** testy Flutter HTTP używają atrap odpowiedzi; test Android network config sprawdza niezależnie politykę XML. Dopiero uruchomienie klienta na fizycznym telefonie z działającym serwerem GGUF potwierdzi rzeczywistą inferencję.

## Priorytety implementacji od teraz

| Priorytet | Wymóg | Status |
|---|---|---|
| P0 | Import modeli własnych GGUF/safetensors | Flutter: pliki, SHA-256, typy, profile |
| P0 | Lokalny czat z modelem użytkownika bez konta | Flutter: klient HTTP loopback + GET models; wymaga uruchomionego lokalnego model-server |
| P0 | Native Android network config | Skrypt + CI; Android localhost wyjątek |
| P0 | llama.cpp/C++ uruchamiany automatycznie przez aplikację | NIE WDROŻONO; obecnie zewnętrzny proces na urządzeniu |
| P1 | Generowanie obrazu z własnych SDXL/FLUX itp. | Rejestr i kontrakt silnika; biblioteka JNI/FFI niepodłączona |
| P1 | Generowanie wideo z Wan/LTX itp. | GPU worker/codec/NLE NIE WDROŻONE |
| P1 | Ulepszanie oraz ładowanie własnych LoRA, VAE, ref images | PRZYSZŁA IMPLEMENTACJA |
| P2 | Marketplace własnych modeli i narzędzi | PLAN |
| Opcjonalne | REST VisionStory i inne zewnętrzne usługi | Oddzielne adaptery, nie domyślne ani wymagane |

## Zasady projektu UX

Pierwsze ekrany: **Moje modele**, **Czat lokalny**, **Studio obrazu**, **Studio filmowe**, **Audio**. Na kartach: obsługa typów i profili, zainstalowany/niezainstalowany silnik, RAM/GPU, rozmiar i licencja modelu, privacy/offline, pobranie / load / start / stop, zgodność runtime, queue, błąd. Nie pokazywać symulowanego stanu „gotowy” ani nie wymagać logowania do dostawcy.

Główny rejestr do projektowania: \`docs/UI_SCREEN_INTEGRATION_MASTER.md\`.
