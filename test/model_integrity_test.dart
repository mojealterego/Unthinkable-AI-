import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:unthinkable_ai/features/diffusion/model_integrity.dart';

void main() {
  test('Streaming SHA-256 matches published digest for UTF-8 fixture', () async {
    final dir = await Directory.systemTemp.createTemp('unthinkable-hash-');
    try {
      final file = File('${dir.path}/test.gguf');
      await file.writeAsString('abc');
      final digest = await computeFileSha256(file);
      expect(digest, 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
      expect(await verifyFileSha256(file, digest), true);
      await file.writeAsString('changed');
      expect(await verifyFileSha256(file, digest), false);
      expect(await verifyFileSha256(file, 'invalid'), false);
    } finally {
      await dir.delete(recursive: true);
    }
  });

  test('Missing models fail closed rather than claiming valid digests', () async {
    expect(await verifyFileSha256(File('/definitely/missing/unthinkable.gguf'),
      'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'), false);
  });
}
