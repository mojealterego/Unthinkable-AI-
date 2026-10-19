import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:unthinkable_ai/features/web/website_creator_screen.dart';

void main() {
  testWidgets('NoCode editor is usable offline and persists site and sections', (tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(const MaterialApp(home: WebsiteCreatorScreen()));
    await tester.pumpAndSettle();
    expect(find.text('NoCode Website Creator'), findsOneWidget);
    await tester.enterText(find.byKey(const Key('nocode_site_name')), 'Mój portal');
    await tester.ensureVisible(find.byKey(const Key('nocode_add_section')));
    await tester.tap(find.byKey(const Key('nocode_add_section')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('nocode_section_heading')), 'Nowa sekcja');
    await tester.tap(find.byKey(const Key('nocode_save_section')));
    await tester.pumpAndSettle();
    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('unthinkable.nocode.website.v1'), contains('Nowa sekcja'));
    expect(prefs.getString('unthinkable.nocode.website.v1'), contains('Mój portal'));
  });
}
