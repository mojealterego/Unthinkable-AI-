# Przyszłe grafiki dla narzędzi AI

Grafiki przygotowuje właściciel aplikacji. Nie dodawano sztucznych grafik ani cudzych obrazów ze zrzutów VisionStory.

`lib/features/tools/ai_tools_catalog.dart` określa stałe identyfikatory narzędzi i docelowy wzorzec ścieżek. Pliki WEBP można będzie umieszczać w `assets/ai_tools/` pod nazwą `<id>.webp`. Zalecany format: 1200×700 px, jednolity styl Santa Muerte/Unthinkable AI, obszar bez istotnej treści w dolnej części na podpis karty. Lista ID: `video_generator`, `music_video`, `video_face_swap`, `video_matting`, `viral_music`, `animals_video`, `ai_image`, `image_face_swap`, `background_remove`, `audio_extract`, `voice_clone`.

Na razie aplikacja używa ikonek Material zamiast brakujących plików, aby build nie zależał od grafik. Po dostarczeniu assetów należy dodać wpis `flutter/assets:` w `pubspec.yaml`, obsługę `Image.asset` i testy układu. Każdy ekran zachowuje rozróżnienie między realnie działającą funkcją a narzędziem oczekującym na silnik.
