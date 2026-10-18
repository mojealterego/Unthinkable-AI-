import 'package:flutter_test/flutter_test.dart';
import 'package:unthinkable_ai/features/diffusion/model_catalog.dart';
import 'package:unthinkable_ai/features/diffusion/model_manifest.dart';

void main() {
  test('QNN is a separate model format', () {
    final qnn = galaxyS24UltraCandidates.firstWhere((e) => e.format == ModelFormat.qnn);
    expect(qnn.suitability, DeviceSuitability.experimental);
  });
  test('large video models are not advertised as mobile ready', () {
    final large = galaxyS24UltraCandidates.last;
    expect(large.suitability, DeviceSuitability.remoteRecommended);
  });
}
