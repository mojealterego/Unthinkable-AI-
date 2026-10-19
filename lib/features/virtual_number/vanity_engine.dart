import 'dart:math';

/// An internal alias candidate is never an assigned public DID.
enum VanityStyle { repeated, pairs, sequence, random }

class VanityCandidate {
  const VanityCandidate({
    required this.identifier, required this.tier,
    required this.score, required this.entropy,
  });
  final String identifier;
  final String tier;
  final int score;
  final double entropy;
  String get scope => 'on_net_only';
  bool get publiclyRoutable => false;
}

class VanityEngine {
  const VanityEngine();

  String normalize(String value) {
    final clean = value.replaceAll(RegExp(r'[\s().-]'), '');
    if (!RegExp(r'^[0-9]{3,18}$').hasMatch(clean)) {
      throw const FormatException('Alias musi mieć od 3 do 18 cyfr (0–9).');
    }
    return clean;
  }

  int _sameRun(String input) {
    var best = 1;
    var current = 1;
    for (var i = 1; i < input.length; i++) {
      current = input[i] == input[i - 1] ? current + 1 : 1;
      best = max(best, current);
    }
    return best;
  }

  int _stepRun(String input) {
    var best = 1;
    var current = 1;
    var previousStep = 0;
    for (var i = 1; i < input.length; i++) {
      final step = int.parse(input[i]) - int.parse(input[i - 1]);
      if (step.abs() == 1 && (previousStep == 0 || step == previousStep)) {
        current++;
      } else if (step.abs() == 1) {
        current = 2;
      } else {
        current = 1;
      }
      previousStep = step.abs() == 1 ? step : 0;
      best = max(best, current);
    }
    return best;
  }

  bool _repeatedBlocks(String digits, int size) {
    if (digits.length < size * 3) return false;
    for (var i = 0; i <= digits.length - size * 3; i++) {
      final b = digits.substring(i, i + size);
      if (digits.substring(i + size, i + size * 2) == b &&
          digits.substring(i + size * 2, i + size * 3) == b) return true;
    }
    return false;
  }

  VanityCandidate evaluate(String input) {
    final digits = normalize(input);
    final frequencies = <String, int>{};
    for (final digit in digits.split('')) {
      frequencies[digit] = (frequencies[digit] ?? 0) + 1;
    }
    var entropy = 0.0;
    for (final count in frequencies.values) {
      final p = count / digits.length;
      entropy -= p * (log(p) / ln2);
    }
    final run = _sameRun(digits);
    final steps = _stepRun(digits);
    late final String tier;
    late final int score;
    if (run >= 6 || steps >= 6) {
      tier = 'PLATINUM';
      score = 100;
    } else if (run >= 4 || steps >= 4 ||
        _repeatedBlocks(digits, 2) || _repeatedBlocks(digits, 3)) {
      tier = 'GOLD';
      score = 80;
    } else if (frequencies.length <= 3) {
      tier = 'SILVER';
      score = 50;
    } else {
      tier = 'STANDARD';
      score = (35 - 8 * entropy).floor().clamp(0, 40);
    }
    return VanityCandidate(
      identifier: digits, tier: tier,
      score: score, entropy: (entropy * 100000).round() / 100000,
    );
  }

  List<VanityCandidate> generate({
    String prefix = '', int length = 9, int count = 8,
    VanityStyle style = VanityStyle.repeated,
  }) {
    if (!RegExp(r'^[0-9]{0,15}$').hasMatch(prefix) ||
        length < 4 || length > 18 || prefix.length >= length ||
        count < 1 || count > 30) {
      throw const FormatException('Nieprawidłowy prefiks, długość lub liczba propozycji.');
    }
    final remaining = length - prefix.length;
    if (style == VanityStyle.repeated && remaining < 2) {
      throw const FormatException('Za krótki wzór dla powtarzanych cyfr.');
    }
    final rng = Random.secure();
    final proposals = <String, VanityCandidate>{};
    for (var iteration = 0; iteration < 300 && proposals.length < count; iteration++) {
      final n = iteration;
      late final String suffix;
      switch (style) {
        case VanityStyle.random:
          suffix = List.generate(remaining, (_) => rng.nextInt(10)).join();
        case VanityStyle.repeated:
          final digit = prefix.isNotEmpty ? prefix[prefix.length - 1] : (n % 10).toString();
          suffix = (digit * (remaining - 1)) + (n % 10).toString();
        case VanityStyle.pairs:
          final block = (n % 10).toString() + (((n ~/ 10) + 3) % 10).toString();
          suffix = (block * (remaining ~/ 2 + 1)).substring(0, remaining);
        case VanityStyle.sequence:
          suffix = List.generate(remaining, (i) => (n + i) % 10).join();
      }
      final number = prefix + suffix;
      proposals.putIfAbsent(number, () => evaluate(number));
    }
    if (proposals.length < count) {
      throw const FormatException('Za mało różnych propozycji. Zmień długość lub wzór.');
    }
    final output = proposals.values.toList();
    output.sort((a, b) {
      final byScore = b.score.compareTo(a.score);
      return byScore != 0 ? byScore : a.identifier.compareTo(b.identifier);
    });
    return output;
  }
}
