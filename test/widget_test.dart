import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:unthinkable_ai/main.dart';

void main() {
  testWidgets('Renders module register dashboard', (tester) async {
    await tester.pumpWidget(const UnthinkableAiApp());
    expect(find.text('Katalog funkcji • 27 obszarów'), findsOneWidget);
    expect(find.text('Unthinkable AI'), findsOneWidget);
  });

  testWidgets('Filters domains using Polish text', (tester) async {
    await tester.pumpWidget(const UnthinkableAiApp());
    await tester.enterText(find.byKey(const Key('search_domains')), 'Pinokio');
    await tester.pumpAndSettle();
    expect(find.text('Studio filmowe'), findsOneWidget);
    expect(find.text('Game Builder'), findsNothing);
  });
}
