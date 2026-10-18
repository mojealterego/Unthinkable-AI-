import 'model_manifest.dart';

/// Hardware guidance only. Not proof of runtime support.
enum DeviceSuitability { candidate, experimental, remoteRecommended }

class ModelCandidate {
  const ModelCandidate(this.family, this.format, this.suitability, this.notes);
  final String family;
  final ModelFormat format;
  final DeviceSuitability suitability;
  final String notes;
}

const galaxyS24UltraCandidates = <ModelCandidate>[
  ModelCandidate('Stable Diffusion 1.5', ModelFormat.safetensors,
      DeviceSuitability.candidate, 'First on-device image validation target.'),
  ModelCandidate('SDXL / Illustrious / Pony', ModelFormat.gguf,
      DeviceSuitability.candidate, 'Test quantized weights and peak memory.'),
  ModelCandidate('SDXL Qualcomm QNN', ModelFormat.qnn,
      DeviceSuitability.experimental, 'Requires independent Qualcomm QNN runtime and licensed SDK.'),
  ModelCandidate('FLUX.2 Klein', ModelFormat.gguf,
      DeviceSuitability.experimental, 'Android runtime and memory must be verified.'),
  ModelCandidate('Wan 2.1 T2V 1.3B', ModelFormat.gguf,
      DeviceSuitability.experimental, 'Video memory includes encoders, VAE and activations.'),
  ModelCandidate('Qwen Image 2.1', ModelFormat.gguf,
      DeviceSuitability.experimental, 'Text encoder memory may exceed mobile limits.'),
  ModelCandidate('Wan 14B / LTX 2.3 21B', ModelFormat.gguf,
      DeviceSuitability.remoteRecommended, 'Prefer remote GPU; not a mobile-ready claim.'),
];
