# Unthinkable AI — AGENT ENGINEERING RULES

Repozytorium: mojealterego/Unthinkable-AI-; bazowa gałąź: main. Żadnych innych gałęzi bez decyzji właściciela.

1. Zawsze najpierw czytaj aktualny kod, README, docs/SOURCE_AUDIT.md i requirements/requirements.csv. Macierz 339 ID jest minimalną podstawą audytu, nie zapewnieniem implementacji.
2. Zbieraj dokładne źródła, wersje/licencje, komendy testów, artefakty dowodowe i SHA. Nie pomijaj ani nie zamieniaj wymagań bez decision log.
3. Nie ogłaszaj produkcyjności ani ukończenia bez rzeczywistego kompilatora, testów, logów i odbioru. Nie traktuj dekompilacji cudzej APK jako licencjonowanego źródła.
4. Do kodu pisz najmniejsze bezpieczne commity. Przed zapisem sprawdzaj HEAD i stosuj optimistic locking; unikaj uszkodzenia równoległych zmian.
5. DGM/RSI może sam wykrywać problemy i przygotowywać poprawki, ale rollout, uprawnienia do sekretów, produkcyjne płatności i zmiany krytyczne wymagają niezależnej walidacji i polityki akceptacji.
6. Przewiduj brak dostępu do GPU, praw do modeli, pieniędzy i uprawnień Android. Zamiast fikcyjnych wyników oznaczaj BLOCKED.
7. Model uncensored/abliterated/NSFW to profil modelu i dystrybucji; nie obejście przepisów ani zabezpieczeń małoletnich.
8. Dowolny alias telefoniczny może być identyfikatorem wewnętrznym; publiczny numer i caller ID wymagają realnego przydziału/weryfikacji.
9. Tor ma chronić prywatność, ale nie gwarantuje anonimowości. Nie realizuj nadużyć numerów, deanonimizacji czy nieautoryzowanego scrapingu.
10. Preferowane granice: Flutter/Dart frontend, Rust policies/runtime, C++ inference FFI, Python research/workers, cloud GPU queues, signed extensions, audytowane MCP adapters.

Systemowe wyniki każdej iteracji: zmienione pliki, SHA, testy, źródła, niezaliczone kryteria, zmapowane requirement IDs i następne zadania.

## Obowiązkowa zasada ciągłego wzbogacania systemu (polecenie właściciela, 2026-10-19)

**Każdy nowy dokument, PDF, opis API, repozytorium lub polecenie użytkownika jest wejściem do procesu implementacji, nie tylko do raportowania.**

1. Analizuj źródła po kolei i strona po stronie, nadaj trwały identyfikator oraz przypisz każdą nową funkcję do zakresu wymagań i odpowiednich ekranów UI. Zachowaj oryginalne nazwy kontraktów API i oddzielaj oficjalne schematy od propozycji.
2. Porównaj każdą funkcję z rzeczywistym kodem bieżącego `main` i wynikami CI. Oznacz `EXISTS_VERIFIED`, `PARTIAL`, `MISSING`, `BLOCKED` albo `DUPLICATE` wraz z dowodem. Nie uznawaj obecności karty UI za wdrożoną funkcjonalność.
3. **Dla `MISSING` i `PARTIAL` automatycznie implementuj bezpieczną, możliwą do zweryfikowania brakującą funkcję**. Obejmij kod, migracje danych, testy jednostkowe/integracyjne, podłączenie backendu do ekranu, aktualizację dokumentacji i mapy UI. Nie ograniczaj się do zadań w Roadmapie.
4. Wprowadzaj niezależne, małe zmiany na `main` i sprawdzaj konflikty HEAD przy każdej publikacji. Nie nadpisuj równolegle powstałych modułów; najpierw scalaj i uruchamiaj testy regresji.
5. Jeśli integracja wymaga brakującego klucza API, konta, limitu GPU, praw do danych, licencji lub dostępu infrastrukturalnego — wykonaj wszystkie dostępne niepłatne kroki, przygotuj bezpieczny adapter i testy z atrapą dostawcy, a resztę oznacz `BLOCKED` z konkretną zależnością. Nie wpisuj sekretów do czatu/repozytorium ani nie wykonuj płatnych operacji bez zgody.
6. Z każdym dokumentem ulepszaj architekturę i ergonomię, kiedy jest ku temu uzasadnienie techniczne; nie wymagaj nowego pytania właściciela przy zwykłych ulepszeniach kodu. Odróżniaj je od zmian wymagających rzeczywistej autoryzacji lub nowego wydatku.
7. Właściciel dostarcza finalny wygląd i grafiki UI oddzielnie. Aktualizuj od razu nazwy ekranów, wejścia/wyjścia, zależności, stany i sloty assetów; nie zastępuj autorskiego projektu przypadkowymi grafikami.
8. Nie ogłaszaj zakończenia całego produktu, dopóki pełny audyt źródeł, integracja i odbiór nie są potwierdzone. Po każdej iteracji podawaj dokładne commity, testy CI, brakujące funkcje i blokady.

Dla VisionStory szczegóły źródłowe i rozszerzenia znajdują się w `requirements/visionstory_sources.csv`, `docs/VISIONSTORY_BATCH_02_AUDIT.md` oraz `docs/UI_SCREEN_INTEGRATION_MASTER.md`. Dokumentacja jest otwarta — użytkownik zapowiedział co najmniej 60 kolejnych plików.
