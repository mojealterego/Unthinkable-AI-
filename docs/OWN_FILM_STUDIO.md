# Unthinkable Film Studio — własne silniki, bez VisionStory

## Obowiązująca architektura

VisionStory i jego dokumentacja stanowią materiał referencyjny funkcji. Nie są dostawcą produkcyjnym, a nasze Studio Filmowe nie wymaga konta, kredytów ani klucza VisionStory.

Pierwszy rzeczywisty silnik montażu działa na własnym serwerze przez FFmpeg. Nasze modele generatywne (Wan/LTX/ODYN), awatary, lip-sync, voice clone, face-swap i pełne NLE to odrębne komponenty do ukończenia, a nie udawane możliwości FFmpeg.

## Działające API własnego backendu

| Metoda | Endpoint | Funkcja |
|---|---|---|
| GET | /api/film-studio/capabilities | Gotowość własnych zasobów i prawdziwy stan funkcji |
| POST | /api/film-studio/assets | Import własnych MP4, MP3, WAV, JPEG i PNG do 160 MiB |
| GET | /api/film-studio/assets | Lista prywatnych mediów |
| POST | /api/film-studio/timeline/validate | Kontrola kolejności, długości i mediów |
| POST | /api/film-studio/timeline/render | Faktyczny render FFmpeg: H.264, łączenie scen, soundtrack MP3/WAV |
| GET | /api/film-studio/jobs/{job_id} | Stan kolejki SQLite |
| GET | /api/film-studio/jobs/{job_id}/file | Pobranie ukończonego MP4 |

Zadania są prowadzone na serwerze użytkownika; brak żądań do VisionStory. Render jest wykonywany asynchronicznie w jednym wątku procesu. Wersja testowa pozwala tworzyć projekty do 12 godzin, ale bez potwierdzenia wydajności 123-minutowej produkcji.

## Konfiguracja własnego serwera

Dockerfile zawiera FFmpeg. Ustaw UNTHINKABLE_FILM_ROOT jako absolutną ścieżkę do prywatnego, zapisywalnego trwałego wolumenu (np. /data/film_studio) i osobny sekret API_KEY naszego backendu. Konfiguracja reverse proxy HTTPS pozostaje po stronie właściciela infrastruktury. Nie potrzeba VISIONSTORY_API_KEY.

Zewnętrzne trasy VisionStory są domyślnie WYŁĄCZONE. Można je świadomie włączyć wyłącznie do historycznych testów archiwalnego kodu ustawiając UNTHINKABLE_ENABLE_LEGACY_VISIONSTORY=1. Główna aplikacja nie powinna udostępniać ich jako funkcji studia.

## Rzeczywiste braki

- Native Wan/LTX video inference, ODYN GPU worker, model registry, sterowanie VRAM i job scheduler.
- Spójna postać, generowanie awatarów i twarzy, kontrolowane face swap, lipsync.
- Beat detection i inteligentna synchronizacja do MP3 (aktualnie możliwe tylko połączenie utworu z ujęciami).
- Pełne wielościeżkowe NLE, keyframes, maski, VFX, tytuły i automatyczny montaż.
- Flutter — własny ekran do importu, renderu i pobrania (do podłączenia).
- Multi-tenancy i ACL: obecny wspólny API_KEY NIE izoluje danych wielu użytkowników.
- Trwały worker na wielu hostach i recovery: obecny render działa w jednym procesie.

## Wytyczne UI dla projektanta

Studio filmowe: projekty, scenariusze, referencje, własne modele, awatary, ujęcia, timeline, MP3 Music Video, generowanie własnym GPU, rendering, biblioteka MP4 i QC. Nie projektować logowania lub salda VisionStory jako wymagań głównego produktu. Grafikę i docelowe UI dostarcza właściciel.

Test: tests/test_film_studio.py — w tym prawdziwy FFmpeg MP4+MP3 na maszynie z FFmpeg.
