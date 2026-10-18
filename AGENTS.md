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
