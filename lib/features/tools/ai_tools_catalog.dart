import 'package:flutter/material.dart';

enum StudioCategory { all, video, image, audio }
enum StudioLaunch { filmStudio, modelLibrary, requiresEngine }

class AiStudioTool {
  const AiStudioTool({
    required this.id, required this.title, required this.description,
    required this.category, required this.icon, required this.launch,
    this.featured = false,
  });

  final String id;
  final String title;
  final String description;
  final StudioCategory category;
  final IconData icon;
  final StudioLaunch launch;
  final bool featured;

  /// Naming convention for artwork provided by the project owner.
  String get artworkSlot => 'assets/ai_tools/' + id + '.webp';
}

const aiStudioTools = <AiStudioTool>[
  AiStudioTool(
    id: 'video_generator', title: 'Generator wideo AI',
    description: 'Projektuj sceny, aktorów i montaż filmu. Render wymaga silnika.',
    category: StudioCategory.video, icon: Icons.movie_creation_outlined,
    launch: StudioLaunch.filmStudio, featured: true,
  ),
  AiStudioTool(
    id: 'music_video', title: 'Teledysk',
    description: 'Zamień muzykę w plan ujęć i historię wizualną.',
    category: StudioCategory.video, icon: Icons.music_video_outlined,
    launch: StudioLaunch.filmStudio, featured: true,
  ),
  AiStudioTool(
    id: 'video_face_swap', title: 'Podmiana twarzy w wideo',
    description: 'Wymaga modelu, zgody osób i kontroli referencji.',
    category: StudioCategory.video, icon: Icons.face_retouching_natural,
    launch: StudioLaunch.requiresEngine, featured: true,
  ),
  AiStudioTool(
    id: 'video_matting', title: 'Matting wideo AI',
    description: 'Wycinanie obiektów i tła z klipów.',
    category: StudioCategory.video, icon: Icons.video_settings_outlined,
    launch: StudioLaunch.requiresEngine,
  ),
  AiStudioTool(
    id: 'viral_music', title: 'Wiralowa muzyka',
    description: 'Synchronizacja utworu, awatara i choreografii.',
    category: StudioCategory.video, icon: Icons.mic_external_on_outlined,
    launch: StudioLaunch.requiresEngine,
  ),
  AiStudioTool(
    id: 'animals_video', title: 'Wideo ze zwierzętami',
    description: 'Generowanie scen z referencjami zwierząt.',
    category: StudioCategory.video, icon: Icons.pets_outlined,
    launch: StudioLaunch.requiresEngine,
  ),
  AiStudioTool(
    id: 'ai_image', title: 'Obraz AI',
    description: 'Zarządzaj lokalnymi modelami i adapterami obrazowymi ODYN.',
    category: StudioCategory.image, icon: Icons.auto_awesome_motion_outlined,
    launch: StudioLaunch.modelLibrary,
  ),
  AiStudioTool(
    id: 'image_face_swap', title: 'Podmiana twarzy na obrazie',
    description: 'Edycja wizerunku za zgodą osób przedstawionych.',
    category: StudioCategory.image, icon: Icons.face_retouching_natural,
    launch: StudioLaunch.requiresEngine,
  ),
  AiStudioTool(
    id: 'background_remove', title: 'Usuń tło',
    description: 'Segmentacja i usuwanie tła zdjęć.',
    category: StudioCategory.image, icon: Icons.layers_clear_outlined,
    launch: StudioLaunch.requiresEngine,
  ),
  AiStudioTool(
    id: 'audio_extract', title: 'Wyodrębnianie audio z wideo',
    description: 'Konwersja ścieżki dźwiękowej do pliku audio.',
    category: StudioCategory.audio, icon: Icons.audio_file_outlined,
    launch: StudioLaunch.requiresEngine,
  ),
  AiStudioTool(
    id: 'voice_clone', title: 'Klonowanie głosu',
    description: 'Modelowanie głosu wyłącznie za zgodą jego właściciela.',
    category: StudioCategory.audio, icon: Icons.record_voice_over_outlined,
    launch: StudioLaunch.requiresEngine,
  ),
];

List<AiStudioTool> toolsForCategory(StudioCategory category) =>
    category == StudioCategory.all
        ? aiStudioTools
        : aiStudioTools.where((item) => item.category == category).toList();
