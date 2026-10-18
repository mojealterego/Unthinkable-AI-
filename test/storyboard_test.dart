import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:unthinkable_ai/features/video/storyboard.dart';

void main() {
  test('project roundtrips all scene references and timeline duration', () {
    final original = FilmProject(title: 'Film', masterPrompt: 'Stałe światło', shots: [
      FilmShot(id: 's1', name: 'Intro', durationSeconds: 7200, approved: true,
        actorReference: 'A-1', mediaReference: 'clip.mp4', prompt: 'Close-up'),
      FilmShot(id: 's2', name: 'Finał', durationSeconds: 180),
    ]);
    final restored = FilmProject.fromJson(jsonDecode(jsonEncode(original.toJson())) as Map<String, dynamic>);
    expect(restored.durationSeconds, 7380);
    expect(restored.isAtLeast123Minutes, isTrue);
    expect(restored.approvedShots, 1);
    expect(restored.masterPrompt, 'Stałe światło');
    expect(restored.shots.first.actorReference, 'A-1');
    expect(restored.shots.first.mediaReference, 'clip.mp4');
    expect(formatFilmDuration(7380), '02:03:00');
  });

  test('rejects malformed or unsafe imported durations', () {
    final bad = FilmProject(shots: [
      FilmShot(id: 's1', name: 'Kadr', durationSeconds: 30),
    ]).toJson();
    ((bad['shots'] as List).first as Map<String, Object>)['durationSeconds'] = -1;
    expect(() => FilmProject.fromJson(bad), throwsFormatException);
  });

  testWidgets('film studio accepts and saves shot data in the UI', (tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(const MaterialApp(home: FilmStudioScreen()));
    await tester.pumpAndSettle();
    expect(find.text('Studio scen i ujęć'), findsOneWidget);
    await tester.tap(find.byKey(const Key('add_shot')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('shot_name')), 'Scena testowa');
    await tester.enterText(find.byKey(const Key('shot_seconds')), '120');
    await tester.tap(find.byKey(const Key('save_shot')));
    await tester.pumpAndSettle();
    expect(find.text('Scena testowa'), findsOneWidget);
    expect(find.textContaining('00:02:00'), findsWidgets);
  });
}
