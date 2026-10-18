# Unthinkable AI — source repository reuse audit
**Discovery:** GitHub repository search for `user:mojealterego`, pages 1–7, on 2026-10-18. The resulting inventory has **633 unique repository names**. The CSV is *name/metadata discovery*, **not** a 633-repository code audit, security review or license clearance. Case-sensitive repository names are retained. Scope includes copied forks of third-party projects, not necessarily original works.

## Source revisions
- `mojealterego/Agentic-Cinema-The-Blockbuster-Hackathon`: `04424922b2c6aa77a8d7ce7d3653e0ba6a62cb48`
- `mojealterego/Android-AI-Studio`: `11db8dd28fecaba156a9a748d47c3831dbdf248c`
- `mojealterego/ODYN-Diffusion-Android`: `2c9cad92daea48819dc440d0523f5ec5b84fc773`

## Confirmed integration scope
- ODYN-Diffusion-Android: transferred Dart model manifest, registry, model importer, generation-request validation, candidate catalog and adjusted model-library UI. Native C++ runtime **not** migrated or proven. Licensing and SDK compatibility require review before binary distribution.
- Android-AI-Studio: transferred pure Python permission checks and creative-plan orchestration; backend is *not* yet its complete media server; its direct ComfyUI dependency is intentionally **not** imported as the required architecture should allow independent/native model adapters.
- Agentic Cinema: transferred Pydantic evidence/domain models and production operations orchestrator; no live Google ADK runner wired. Preserved explicitly synthetic demo and corrected mislabelled demo MCP evidence.

## High-priority follow-up, **not yet incorporated**
- Image/video: `Local-Diffusion`, `stable-diffusion.cpp`, `LTX-Video`, `OpenMontage`, `Cinematic-Agents`, `HunyuanVideo-I2V`
- Local LLM: `llama.cpp`, `pocketpal-ai`, `LocalAI`, `hermes-mobile`
- Agent platform: `dgm`, `OmniMAS-Advanced`, `open-agent-builder`, `ToolNeuron`, `Graph-of-Thoughts`
- Games: `ai-game-builder`, `GameDev-MCP-Server`, `Godot-AI-Tools-Template`, `Unreal-MCP`, `Unity-MCP2`
- Research/math: `Problemy-milenijne`, `lucidrag`, `graphiti`, `agent-evaluation-lab`
- Audio: `Giant-Music-Transformer`, `OpenMusic`, `elevenlabs-android`

## Admission gate for every additional code migration
1. Check source repo head, nested `LICENSE`, authorship and upstream fork history. Access to a fork does not override an upstream GPL/AGPL/commercial license.
2. Verify code paths, actual executed behavior vs placeholder/demo, tests, secret handling and supply-chain dependencies.
3. Keep copied source namespaced, preserve provenance/revision, do not overwrite existing entrypoints, put behavior behind explicit capability and consent policy.
4. Run language-appropriate CI with real logs; native GPU/mobile claims require measured target-device tests.
5. Never bulk-import exploit kits, remote-access trojans, surveillance/malware material or credential-harvesting code into the general consumer app.

See `docs/REUSE_INVENTORY.csv` for all 633 discovered names and triage state.
