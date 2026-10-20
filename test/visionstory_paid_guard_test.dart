import 'dart:async';
import 'dart:io';

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
    // Flutter scrollUntilVisible can stop with the button partly beneath the
    // screen's lower edge. Move it into the real tappable viewport.
    await tester.ensureVisible(resetButton);
    await tester.drag(find.byType(ListView).last, const Offset(0, -160));
    await tester.pumpAndSettle();
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
  test('Local VisionStory SRT export writes UTF-8 and rejects empty tracks',
      () async {
    final directory = await Directory.systemTemp.createTemp('visionstory-srt-');
    addTearDown(() => directory.delete(recursive: true));
    const content = '1\n00:00:00,000 --> 00:00:01,000\nZażółć gęślą\n';
    final stored = await saveVisionStorySrt(content, directory: directory);
    expect(stored.path.endsWith('.srt'), true);
    expect(await stored.readAsString(), content);
    await expectLater(
      saveVisionStorySrt('', directory: directory),
      throwsFormatException,
    );
    await expectLater(
      saveVisionStorySrt('x' * (1024 * 1024 + 1), directory: directory),
      throwsFormatException,
    );
  });

  test('VisionStory gateway does not forward bearer tokens through redirects', () async {
    var requests = 0;
    final client = VisionStoryGateway(client: MockClient((request) async {
      requests++;
      expect(request.url.toString(),
          'https://studio.example/api/cinema/visionstory/credits');
      expect(request.headers['Authorization'], 'Bearer secret-gateway');
      expect(request.followRedirects, false);
      expect(request.maxRedirects, 0);
      return http.Response('', 302, headers: {
        'location': 'https://another.example/steal-token',
      });
    }));
    await expectLater(
      client.call(server: 'https://studio.example',
          key: 'secret-gateway', path: 'credits'),
      throwsA(isA<VisionStoryGatewayError>()),
    );
    expect(requests, 1);
    client.close();
  });

  test('VisionStory JSON responses larger than three MiB are rejected', () async {
    final client = VisionStoryGateway(client: MockClient((request) async {
      return http.Response('x' * (3 * 1024 * 1024 + 1), 200);
    }));
    await expectLater(
      client.call(server: 'https://studio.example',
          key: 'gateway-key', path: 'credits'),
      throwsA(isA<VisionStoryGatewayError>()),
    );
    client.close();
  });

  testWidgets('Changing the clip prompt while quote is in flight invalidates it',
      (tester) async {
    SharedPreferences.setMockInitialValues({});
    final quoteReply = Completer<http.Response>();
    var paidPosts = 0;
    final client = VisionStoryGateway(client: MockClient((request) async {
      if (request.url.path.endsWith('/ai-video/estimate')) return quoteReply.future;
      if (request.url.path.endsWith('/ai-video')) paidPosts++;
      return http.Response('{"error":"unexpected request"}', 500);
    }));
    await tester.pumpWidget(
        MaterialApp(home: VisionStoryStudioScreen(gateway: client)));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Prywatny backend HTTPS'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('visionstory_url')),
        'https://studio.example');
    await tester.enterText(find.byKey(const Key('visionstory_gateway_key')),
        'gateway-key');
    await tester.tap(find.text('Wideo'));
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(const Key('visionstory_clip_model')),
        'seedance-2.0');
    await tester.enterText(find.byKey(const Key('visionstory_clip_prompt')),
        'Pierwszy opis klipu');
    final list = find.descendant(
      of: find.byType(ListView).last,
      matching: find.byType(Scrollable),
    ).first;
    await tester.scrollUntilVisible(
      find.byKey(const Key('visionstory_quote')),
      150, scrollable: list, maxScrolls: 20,
    );
    await tester.ensureVisible(find.byKey(const Key('visionstory_quote')));
    await tester.tap(find.byKey(const Key('visionstory_quote')));
    await tester.pump();
    // Text editors remain usable during backend quote retrieval.
    await tester.scrollUntilVisible(
      find.byKey(const Key('visionstory_clip_prompt')),
      -150, scrollable: list, maxScrolls: 20,
    );
    await tester.ensureVisible(find.byKey(const Key('visionstory_clip_prompt')));
    await tester.enterText(find.byKey(const Key('visionstory_clip_prompt')),
        'Zmieniony opis klipu');
    await tester.pump();
    quoteReply.complete(http.Response('{"credits_estimated":7}', 200));
    await tester.pumpAndSettle();
    expect(find.textContaining('Parametry ujęcia zmieniły się podczas wyceny'),
        findsOneWidget);
    expect(find.text('Wycena: 7 kredytów'), findsNothing);
    await tester.scrollUntilVisible(
      find.byKey(const Key('visionstory_submit_clip')),
      160, scrollable: list, maxScrolls: 20,
    );
    final submit = tester.widget<FilledButton>(
        find.byKey(const Key('visionstory_submit_clip')));
    expect(submit.onPressed, isNull);
    expect(paidPosts, 0);
    client.close();
  });

}
