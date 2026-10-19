import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:unthinkable_ai/features/virtual_number/vanity_engine.dart';
import 'package:unthinkable_ai/features/virtual_number/virtual_number_screen.dart';

void main() {
  test('Candidate scores do not confuse alternating pairs with a monotonic run', () {
    const engine = VanityEngine();
    expect(engine.evaluate('777777777').tier, 'PLATINUM');
    expect(engine.evaluate('12121212').tier, 'GOLD');
    expect(engine.evaluate('12345678').tier, 'PLATINUM');
    expect(engine.evaluate('501 456 456').identifier, '501456456');
    expect(engine.evaluate('000111222').publiclyRoutable, false);
  });

  test('Unrestricted prefixes include 000 and 111 (on-net only)', () {
    const engine = VanityEngine();
    for (final prefix in ['000', '111', '798', '666']) {
      final rows = engine.generate(prefix: prefix, length: 10, count: 8);
      expect(rows.length, 8);
      expect(rows.map((e) => e.identifier).toSet().length, 8);
      expect(rows.every((e) => e.identifier.startsWith(prefix)), isTrue);
      expect(rows.every((e) => e.scope == 'on_net_only'), isTrue);
    }
  });

  test('No E.164 assignment or invalid prefixes', () {
    const engine = VanityEngine();
    expect(() => engine.evaluate('+48501111222'), throwsFormatException);
    expect(() => engine.generate(prefix: '12x', length: 9), throwsFormatException);
    expect(() => engine.generate(prefix: '123456789', length: 9), throwsFormatException);
  });

  testWidgets('Generated candidates can be saved to local preferences', (tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(const MaterialApp(home: VirtualNumberScreen()));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('vanity_prefix')), '111');
    await tester.ensureVisible(find.byKey(const Key('generate_aliases')));
    await tester.tap(find.byKey(const Key('generate_aliases')));
    await tester.pumpAndSettle();
    expect(find.text('Kandydaci — bez rezerwacji'), findsOneWidget);
    final save = find.byTooltip('Zapisz alias').first;
    await tester.ensureVisible(save);
    await tester.tap(save);
    await tester.pumpAndSettle();
    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getStringList('unthinkable.onnet_aliases.v1'), isNotEmpty);
  });
}
