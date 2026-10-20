import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:unthinkable_ai/features/video/visionstory_gateway.dart';
import 'package:unthinkable_ai/features/video/visionstory_studio_screen.dart';

void main() {
  testWidgets('Advanced Studio remembers ambiguous paid jobs across app restarts',
      (tester) async {
    SharedPreferences.setMockInitialValues({
      'unthinkable.visionstory.advanced.paid.avatar': true,
      'unthinkable.visionstory.advanced.paid.avatarId': 'avatar_previous001',
      'unthinkable.visionstory.advanced.paid.clip': true,
      'unthinkable.visionstory.advanced.paid.clipId': 'clip_previous001',
    });
    var outbound = 0;
    final client = VisionStoryGateway(client: MockClient((request) async {
      outbound++;
      return http.Response('{"error":"unexpected network call"}', 500);
    }));
    await tester.pumpWidget(MaterialApp(
      home: VisionStoryStudioScreen(gateway: client),
    ));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Wideo'));
    await tester.pumpAndSettle();

    // The long form is lazily built: scroll the actual vertical editor.
    final editorScroll = find.descendant(
      of: find.byType(ListView).last,
      matching: find.byType(Scrollable),
    ).first;
    await tester.scrollUntilVisible(
      find.byKey(const Key('visionstory_submit_avatar')),
      220,
      scrollable: editorScroll,
      maxScrolls: 30,
    );
    final avatar = tester.widget<OutlinedButton>(
      find.byKey(const Key('visionstory_submit_avatar')),
    );
    expect(avatar.onPressed, isNull);
    await tester.scrollUntilVisible(
      find.byKey(const Key('visionstory_new_paid_job')),
      220,
      scrollable: editorScroll,
      maxScrolls: 30,
    );
    final resetButton = find.byKey(const Key('visionstory_new_paid_job'));
    expect(resetButton, findsOneWidget);
    expect(outbound, 0);

    // Only a separate, clearly-worded action can unlock a new paid job.
    await tester.tap(resetButton);
    await tester.pumpAndSettle();
    expect(find.text('Nowe płatne zlecenie?'), findsOneWidget);
    // The dialog requires separate confirmation; no network operation occurs.
    await tester.tap(find.text('Zatwierdź'));
    await tester.pumpAndSettle();
    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getBool('unthinkable.visionstory.advanced.paid.avatar'), false);
    expect(prefs.getBool('unthinkable.visionstory.advanced.paid.clip'), false);
    expect(prefs.getString('unthinkable.visionstory.advanced.paid.avatarId'), isNull);
    expect(prefs.getString('unthinkable.visionstory.advanced.paid.clipId'), isNull);
    expect(outbound, 0);
  });
}
