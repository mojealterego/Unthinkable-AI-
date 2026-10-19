import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:unthinkable_ai/features/tools/ai_tools_catalog.dart';
import 'package:unthinkable_ai/features/tools/ai_tools_screen.dart';

void main() {
  test('Screen registry has no imaginary deployed audio/video inference', () {
    expect(toolsForCategory(StudioCategory.video).length, greaterThanOrEqualTo(5));
    expect(toolsForCategory(StudioCategory.audio).length, 2);
    final voice = aiStudioTools.singleWhere((x) => x.id == 'voice_clone');
    expect(voice.launch, StudioLaunch.requiresEngine);
    expect(voice.artworkSlot, 'assets/ai_tools/voice_clone.webp');
  });

  testWidgets('Categorized AI tools navigate and show truthful engine state', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: AiToolsScreen()));
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(find.byKey(const Key('studio_tab_audio')), 260,
      scrollable: find.byType(Scrollable).first);
    await tester.ensureVisible(find.byKey(const Key('studio_tab_audio')));
    await tester.tap(find.byKey(const Key('studio_tab_audio')));
    await tester.pumpAndSettle();
    expect(find.text('Klonowanie głosu'), findsOneWidget);
    expect(find.text('Generator wideo AI'), findsNothing);
    await tester.ensureVisible(find.byKey(const Key('ai_tool_voice_clone')));
    await tester.tap(find.byKey(const Key('ai_tool_voice_clone')));
    await tester.pumpAndSettle();
    expect(find.textContaining('nie został jeszcze wdrożony'), findsOneWidget);
  });
}
