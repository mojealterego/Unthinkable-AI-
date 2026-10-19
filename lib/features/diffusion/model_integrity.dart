import 'dart:io';
import 'package:crypto/crypto.dart';

/// SHA-256 streaming verification, O(1) retained file data for large models.
Future<String> computeFileSha256(File file) async {
  if (!await file.exists()) {
    throw const FileSystemException('File not found for SHA-256');
  }
  final value = await sha256.bind(file.openRead()).first;
  return value.toString();
}

Future<bool> verifyFileSha256(File file, String expectedSha256) async {
  if (!RegExp(r'^[a-fA-F0-9]{64}$').hasMatch(expectedSha256)) return false;
  if (!await file.exists() || await FileSystemEntity.isLink(file.path)) return false;
  return (await computeFileSha256(file)) == expectedSha256.toLowerCase();
}
