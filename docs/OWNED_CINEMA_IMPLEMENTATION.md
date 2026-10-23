# Unthinkable Cinema — samodzielny system filmowy

Cel właściciela: nasze Studio Filmowe jest niezależne od VisionStory i innych kont dostawców. Ich PDF-y służą do analizy funkcji, a nie jako obowiązkowy backend.

Moduł services/cinema/owned_studio.py realizuje własne przyjmowanie MP4/MOV oraz MP3/WAV/M4A, montaż cut/concat, dopasowanie rozdzielczości i FPS, ścieżkę muzyczną oraz eksport MP4 przy pomocy samodzielnie zarządzanego FFmpeg.

Ścieżki serwera: GET /api/cinema/owned/capabilities, PUT /api/cinema/owned/assets/{asset_id}?extension=mp4, POST /api/cinema/owned/renders, GET /api/cinema/owned/renders/{render_id}, GET /api/cinema/owned/renders/{render_id}/file. Wszystkie wymagają naszego API_KEY, a żadne nie pobierają kredytów i kluczy VisionStory.

Skonfiguruj UNTHINKABLE_CINEMA_MEDIA_DIR jako absolutny prywatny katalog na trwałym wolumenie. Worker musi mieć zainstalowane FFmpeg z libx264/aac. Render działa asynchronicznie przez BackgroundTasks, aktualizuje plik statusu JSON i zapewnia idempotencję request_id; obsługa restartów oraz kolejka multi-host nadal wymagają implementacji.

Bezpieczeństwo: brak URL w materiałach wejściowych, wyłącznie identyfikatory assetów; upload strumieniowy do 512 MiB, walidacja nagłówka, pliki bez nadpisywania, FFmpeg bez shell i z ograniczeniem protokołów file,pipe; jawne zatwierdzenie własnej mocy obliczeniowej i praw do mediów.

Rzeczywiste ograniczenia: to działający backend montażowy, nie własny generator modeli. Nie ma jeszcze inferencji Wan/ODYN/LTX, pełnego NLE wielościeżkowego, automatycznego klipu do bitu, generatorów awatarów ani zamiany twarzy. Złożenie projektu do 12 godzin nie potwierdza wyrenderowania filmu pełnometrażowego. Brak multi-tenant RBAC i produkcyjnego task-schedulera.

Mapa UI: OWN-01 projekty, OWN-02 import referencji i audio, OWN-03 własne modele generatywne, OWN-04 aktorzy/awatar, OWN-05 NLE timeline, OWN-06 teledysk MP3 i BPM, OWN-07 kolejka, OWN-08 eksport/archiwum. Właściciel przygotuje finalny wygląd.
