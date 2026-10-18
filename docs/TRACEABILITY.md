# Wymagania: nie wolno ich usuwać ani zastępować kategoriami

- `requirements/requirements.csv`: wcześniejszy rejestr 339 pozycji (niepełny).
- `requirements/user-directives.psv`: 146 odrębnych elementów wyodrębnionych z wiadomości użytkownika. Wypisane są jego intencje, lecz sformułowania w pliku mogą być parafrazami, a nie wiernym cytatem.
- `requirements/source-candidates.psv`: 53 *kandydatów* znalezionych w sześciu dokumentach, z numerami stron lub sekcją. Nie oznacza to automatycznej decyzji o wdrożeniu ani braku semantycznego pokrycia przez 339.
- `tools/verify_source_trace.py`: integralność obu list w CI. Nie dowodzi realizacji wymagań.

Zachować osobno: **jawne polecenia właściciela**, **propozycje znalezione w PDF/DOCX**, **potwierdzony kod z testami**. Funkcji nie oznaczać `Done` bez implementacji i dowodu uruchomienia. Żadna opcjonalna pozycja z raportu nie może zostać po cichu zatwierdzona jako żądanie właściciela. Wysokiego ryzyka moduły (medyczne, dziecięce, dane biometryczne, reklama, telekomunikacja, OSINT, erotyka) wymagają osobnej analizy zgód i bezpieczeństwa.

## Dokumenty źródłowe
D1: `Architektura Autonomicznego Systemu DGM - Google Gemini.PDF` (98 s.);
D2: `Taksonomia współczesnych systemów agentowych - Google Gemini.PDF` (109 s., strony 108–109 puste);
D3: `Architektura Systemów Orkiestracji AI.docx` (10 sekcji);
D4: `Ekstremalna Rozbudowa Platformy AI i IDE - Google Gemini.PDF` (21 s.);
D5: `Architektura Systemu Unthinkable AI.pdf` (12 s.);
D6: `Zaprojektuj inżynieryjny prompt dla Deep Research który to wszystko zaprojektuje być może w tych pli - Google Gemini.PDF` (48 s.).

Przed implementacją: mapować każdy `U-xxx` i `X-xxx` na kod, test odbiorczy, licencję, ryzyko, zgody, status i rzeczywisty dowód. Poprzedni prototyp Flutter jest katalogiem. Rozmowa „wszystko zrobić” nie zamienia dokumentu w gotową implementację.
