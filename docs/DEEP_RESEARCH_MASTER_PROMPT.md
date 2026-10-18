# UNTHINKABLE AI — MASTER DEEP RESEARCH & ENGINEERING DIRECTIVE
**Target repository:** https://github.com/mojealterego/Unthinkable-AI-  
**Working branch:** `main` (do not create other branches without explicit authorization)  
**Language:** Polish first; technical names and programmatic identifiers may be English.  
**System state:** Initial requirements audit and repository bootstrap; the app is not yet implemented.

## 0. Execution contract: never omit a source requirement

You are a research-and-engineering system, not a marketing copywriter. Read **all user messages** and **all six attached source documents**, including diagrams, tables, mathematics and code fragments. Read the canonical `requirements/requirements.csv` containing **339 initial requirements across 27 domains**, and `docs/SOURCE_AUDIT.md`. Treat these 339 entries as a **minimum source-derived starting inventory, not a cap**.

For each distinct requirement: preserve exact meaning; assign stable ID; cite originating document/section/page or user message; identify target subsystem, files and interfaces; provide architecture, measurable acceptance test, threat model, compute budget and evidence status. Discover additional requirements in the inputs, APPEND new IDs, never silently delete requirements. Do not merge different Code/NoCode builders, multimedia engines or owner-only modules. Detect discrepancies and record decisions in `docs/DECISIONS.md`. Where document text describes code as "fully production ready" without compiler and runtime evidence, classify as unverified sample.

Maintain `requirements/traceability.csv` with columns: ID, domain, source, source_page_or_message, exact_evidence, specification, owner, package, implementation_files, tests, dependencies, risks, status, evidence_links. Accepted states: SOURCE_DISCOVERED, RESEARCHED, DESIGNED, CODED, TESTED, INTEGRATED, DEPLOYED, ACCEPTED, BLOCKED; moving between states requires evidence. Distinguish source assertions, external verification, engineering hypotheses and achieved results.

## 1. Research procedure

1. Inventory the **entire** checked-out Git tree and commit history on `main`; use actual API metadata and file hashes; avoid treating the decomposed Flutter APK and reports as a complete source repository.
2. Inspect six supplied source documents completely; for PDF/DOCX code blocks and mathematical symbols reconcile parsed text with rendered pages. Extract code into version-controlled candidate files only after checking truncation, license and syntax. Identify every missing file, dependency, native library, asset and manifest.
3. For every external claim search primary-source specifications, official upstream repositories and papers. Record version/tag/commit/hash, license, release date, model checkpoint, API contract, hardware support and working link. Do not assume a public release named "Wan 3.0" exists without primary evidence; similarly verify Pinokio, Godot, Unity, Unreal and every MCP server.
4. Use a source confidence matrix. Flag stale/deprecated libraries (including multimedia codecs and FFmpeg wrappers), availability of build tools and mobile app-store policy.
5. Compile real code in available environments; run tests; record commands, timestamps, CI run IDs and artifacts. If hardware, access, credentials, software, file or asset is missing, mark BLOCKED, and still complete all independent specification and implementation work.
6. Research and implementation may run concurrently as separate sandboxed jobs. Do not claim always-on activity unless an actual deployed runner, scheduler and observability system exists.

## 2. Product and full feature matrix — do not discard a single item

### Product, identity, accessibility
Single Unthinkable AI Android-first platform with optional web/desktop and hybrid cloud consoles. Full PL-default multilingual UI and semantic prompt localization; profiles, onboarding, model catalog, unified command launcher, offline/local-first mode, tablets, accessibility, screen-reader controls and resource-efficient operations. AMOLED/obsidian black premium UI, Santa Muerte logo next to "Unthinkable AI", unique owner-provided Santa Muerte portrait per major window, optional woman-as-Santa-Muerte visual variants, and an exactly scripted **8-second intro**: movement; pointing into empty space; animated revealing and glint of brand name; silence gesture; other hand points to small labels "Uncensored", "Abliterated", "NSFW". Assets supplied later: create **slots**, licensing metadata and graceful fallbacks; do not invent that assets have been delivered. Support an initial approval workflow before artwork generation where requested.

### Multimodal model hosting and provider API
Directly downloadable local GGUF via Hugging Face with SHA256, resumable downloads, correct revisions, license/size selection, device profiling RAM/VRAM/NPU/GPU/CPU, graceful out-of-memory recovery, quantified thermal and battery constraints. User-selectable and automatically routed main/aux GGUF models; speculative decoding only for compatible model/tokenizer/sampling setup; local llama.cpp/C++ and Rust FFI, Vulkan/NNAPI/QNN/Metal where supported, cloud fallback on IBM or alternative; provider abstraction for multiple custom API URLs, keys, quotas and logging redaction. Tags "uncensored", "abliterated", "NSFW" are **metadata**, not proof of capabilities or exemptions from policy, privacy, consent, age checks and law. Cover Hugging Face licensing, model registries, checkpoints, LoRA/quantization, prompt presets and rigorous evaluation.

### Advanced reasoning, memory, multi-agent orchestration
Long-context RAG, sparse/dense hybrid search, knowledge graphs with provenance, bitemporal records, episodic/semantic/procedural memory, HDC experiments, source-aware confidence, contradiction handling, NARS, symbolic solvers, task graphs, tree/graph search, ReAct-style planning, iterative evaluation, uncertainty calibration, tool-use policies and multi-agent memory. Survey and select appropriate patterns from AutoGPT, BabyAGI, OpenHands, SWE-agent, MetaGPT, AutoGen, LangGraph, CrewAI, DSPy, LlamaIndex, Letta, semantic kernel, Hermes, Agent-Zero, AI Scientist and source-named frameworks; do not pile up duplicative frameworks without an interface/benchmark case.

### Agents Builder / Extensions factory
Agents Builder **Code and NoCode** (both separate), meta-agent / orchestration / swarm and reusable crews, Agent Skill Creator, Tool Generator, plugin creator, agent-template gallery, tool registry, marketplace publishing, version constraints, schema validation, resource budgets, sandboxing, capability grants, signed packages and rollback. MCP client/server gateway, remote/local tool invocation and secure plugin installation analogous in convenience to ChatGPT plugins, without assuming binary compatibility. Maintain producer/consumer APIs and test harnesses. Include special technical roles for Rust, Flutter, C++, Python, mobile, cloud, testing, verification, design, research, security and finance.

### App Builder + IDE Code/NoCode
Full code editor with syntax/LSP, Git diffs, terminals in isolated runners, builds, testing, preview, file manager, dependency and API integration. Separate App Builder Code and App Builder NoCode for Android, iOS, Windows, macOS, Web and Cloud; hybrid drag-and-drop/visual AST and reversible source generation; build, sign and deliver APK/AAB and other distributables. Include the user-described matrix of **33 niche apps + 33 developer tools** as source-derived candidate products, with detailed specifications; do not label them implemented.

### Image Studio
Direct **image model slot**: Stable Diffusion-compatible and other verified image generators without requiring ComfyUI, with checkpoint/tokenizer/text encoder/VAE/LoRA/control module/scheduler compatibility descriptors, CPU/GPU backends, native inference adapters, model downloads or provider API keys, no forced provider. Text-to-image, image-to-image, inpainting/outpainting, control references, portrait-from-pencil-to-oil/paint, editing, upscale, style controls, aspect ratio, seed, batch, metadata, rights/consent, content flags, master prompt upload, asset versioning and two-step design-preview-approval-generation for portraits and comics.

### Video & film studio
Multiple native video model slots including whatever official Wan revision is **verified** (research "Wan 3.0" instead of presuming availability), other compatible engines, required VAE or other architecture-specific weights, manifest-based version checks; optional **Pinokio** discovery/desktop or worker integration without making ComfyUI mandatory. Text-to-video, image-to-video, reference-image/video/audio/character input, persistent actor bible, reproducible shot prompts/seeds, hairstyle/costume/location/camera/voice profiles, identity consistency validation with consent and measured failure cases; workflow inspired by Google Flow and Picsart, but no claimed parity without feature comparison.

Inside the app: fully fledged **non-linear editor (NLE)**, storyboard, shot list, multi-track audio/video/subtitles/transitions/color/LUT/keyframes/speed/masking/green screen/FX/ADR/sound mix; timeline undo/history, proxies and project save/reopen, multi-shot generation and stitching, checkpointed background renders, long-form output >=123 minutes and no hard time cap besides storage/resource/codec constraints. Export presets (resolution/FPS/bitrate/HDR/codecs); render jobs must be resumable and verify audiovisual sync, color, scene consistency. Distinguish a long composition from one 123-minute generative inference.

Dedicated cinema agent crew: producer, director, writer, story editor, storyboarder, casting, actor-consistency supervisor, cinematographer, art director, animator, editor, colorist, sound engineer, composer, Foley, VFX, subtitles, QC, producer/legal rights. User-uploadable **master prompts** for image and video by project, scene and agent.

### Audio/music/voice
Two-way streaming **voice chat**, ASR/TTS, interrupt/barge-in, speaker diarization, consented voice reference, multilingual output, lip-sync, standalone music generation, sound effects, soundtrack and **automatic music video** pipeline for uploaded/generated tracks, vocal stems, mastering, podcast studio, audiobook production, MP3 export, performance and licensed rights metadata.

### Game Builder Code/NoCode
Projects from early retro text/pixel games, 2D platformers/visual novels, 2.5D through rich 3D up to AAA-targeted workflows; level editor, sprites, PBR materials, rigs, animations, procedurally generated worlds, dialogue trees, assets, shaders, physics, multiplayer scaffolds, testing and package exports. Unified IDE with separate **Code and NoCode** routes. Inspect actual GitHub MCP servers and tested adapter versions for Unity, Godot and Unreal; remote editor/runners may be needed, and proprietary licenses/expensive GPU workflows must be costed. AAA is a scope/quality aspiration requiring teams, optimization and validation, not guaranteed by one button.

### Book/publishing/education/roleplay
Ebooks, EPUB/PDF generation, books and writing assistant, audio books, AI-created children's fairy tales with complete illustrated editable pages and child-safe review, comics from storyboard/project then human approval then rendering, professional portraits and traditional-medium emulation, roleplay characters/personas, interactive fiction and storytelling with IP/age/consent controls. Include document import/export and relevant content tools found in sources.

### Browsing, data extraction and Android
Two independent browsers: standard clear-web and password/biometric-gated Tor/.onion privacy browser, with isolated cookies/storage, leak prevention, explicit network routing, download sandbox and conservative anonymity claims; web access for browsing/research, OSINT, scrapers with scope/rate limits/robots/policies, API wrappers, website builders, promotion/discount-code generation for **authorized campaigns**, email aliases and Google Workspace integration. Android Device Guardian agent uses public Android APIs for battery/storage/network/app health, permissions by task, diagnostics, backups and automation; privilege escalation/root is not presumed or hidden.

### Communications and virtual numbers
Encrypted ephemeral chat rooms created by invitation link or QR, one-time room credentials, expiry/rekey after termination, deletion policies with honest backup/recipient-device limits; chat, voice and file share. Virtual number creator must support **two distinct identifiers**: (1) arbitrary chosen private in-app IDs/prefixes freely selected by the user; (2) publicly callable numbers selected only from **actually available allocated carrier/provider ranges**, with activation, account verification, SIP/WebRTC/PSTN interoperability, lawful forwarding, verified caller-ID/alias masking of private number, priced per provider. Never claim arbitrary invented public number prefixes are routable.

### Private owner workspace and scientific engines
Strongly separated privileged window available only to the owner. FTP (legacy explicitly risk-labelled), SFTP, MCP tool endpoints, Google Drive, local Android shared-folder tunnel with explicit Storage Access Framework permissions, SMBv2/v3, authenticated NAS, encrypted vault/secret registry, **Database Sandbox** with quotas, snapshots and policy. Separate research chat exactly titled **"Millenium Problems & Cain"** (retain requested UI spelling) with specialized persistent math teams targeting seven Clay Millennium Problems and Cain's Jawbone. Lean 4, Coq, Isabelle, Z3, SMT, algebraic tools, proof trees, graph and sequence constraints, experimental search and reproducibility. No fabricated solutions or assertions that known open problems have been solved; independence, formal verification and peer review are mandatory.

### Market, commerce and monetization
Marketplace for complete agents, skills, tools, plugins, MCP servers, app templates, game assets and user-created digital goods; seller onboarding, scanning, signing, review, versions, license, provenance, entitlement, royalty split, billing, VAT/invoices, refund and fraud controls. Price tiers: **Free -> increasingly capable subscription plans**, optional low-cost entry purchase, separate higher-tier upgrades, optional per-use credits and one-time full purchase with explicit cloud-compute fair-use boundary. Research unit economics and propose realistic PLN monthly/yearly prices with sensitivities; PayPal, BLIK via licensed PSP, Revolut Pay, eligible cryptocurrencies via compliant processor, mobile app store billing rules, webhook verification and idempotency. Transparent advertising and affiliate links, opt-in brand placements, referrals and creator commissions; never secretly replace third-party links or hide sponsorship. Financial forecasts must show CAC, churn, LTV, take-rate, GPU unit cost, conversion assumptions and break-even.

### Supplementary items found only in sources
Enumerate every non-user-explicit item (e.g. VR/AR, near-field social interactions, Bluetooth peripheral integrations and enterprise workflows) in a **separate opt-in decision table**: source evidence, fit, privacy/safety implications, cost, recommendation and awaiting-approval status. Do not quietly omit or quietly enable features.

## 3. Architecture, topology, security and source tree

Design a real monorepo; propose and evaluate at least: `apps/android`, `apps/web-console`, `crates/core`, `crates/model-router`, `crates/security`, `crates/zenoh-transport`, `native/llama-bridge`, `services/gateway`, `services/jobs`, `services/billing`, `services/media-worker`, `services/research`, `agents/github-engineer`, `agents/film-crew`, `agents/maths-lab`, `packages/sdk`, `packages/plugin-contracts`, `infra/ibm`, `infra/kubernetes`, `infra/observability`, `requirements`, `docs`, `tests`, `assets`, `.github/workflows`. Split modules by bounded context, not arbitrary file count. Specify interfaces (OpenAPI/Protobuf/JSON Schema), wire formats, event IDs, idempotency/fencing, tenancy boundaries, authentication, tenancy isolation, GPU scheduler and cost controls. Document file-by-file implementation ownership.

Threat model: prompt injection; malicious MCP/plugins; model supply-chain poisoning; SSRF; RCE; Tor proxy leaks; key storage; cloud/IAM privilege; secrets in Git; device permissions; copyrighted media; voice/actor likeness; payment fraud; malware distribution; child users; moderation/legal regimes. Use least privilege, attestation where available, signed artifacts, fine-grained OAuth, audit trails, KMS/Keystore, zero trust, transparent policy and deletion semantics. Model/extension provenance and permissions are independent of whether weights are called "uncensored".

Infra must compare local Android, rented GPU cloud and IBM Cloud, list SKUs/VRAM/network/storage estimates, background worker orchestration, autoscaling, queues, PostgreSQL/object store, cache, backup, migrations, observability, disaster recovery, SLOs, regional compliance and exit strategy. Set separate environments dev/stage/prod, realistic cost caps and verification of actual provider availability.

## 4. Mathematical formalization and experimental truth

Provide a typed mathematical appendix for **each algorithm actually used**, with assumptions, variable definitions, units, complexity, numerically stable reference algorithm, proof obligations and reproducible benchmarks. Include, when genuinely applicable:
- DGM/RSI candidate transition `S[t+1] = VerifyAndPromote(S[t], proposal, tests, rollbackPlan)`; score quality with confidence intervals and resource constraints, not magical monotonic intelligence.
- Variational free energy `F(q,o) = E_q[log q(s) - log p(o,s)]`, its assumptions and calibration against simpler alerting rules; optional active inference.
- Speculative decoding `alpha(x)=min(1,p(x)/q(x))` **plus correct residual sampling**; tokenizer/KV compatibility and total memory cost. Never assume draft and target can share KV tensors without proof.
- Constrained model routing: maximize observed task-quality/latency/energy/cost subject to RAM/VRAM, thermals and price budgets; Pareto frontier and fallback.
- Scheduling GPU/video jobs: deadline, VRAM, memory bandwidth, chunk/retry and cost constraints; stochastic runtime models where needed.
- Scene consistency: measurable identity/pose/voice/style and continuity losses, reference embeddings only with permission, human review thresholds.
- NLE timecode arithmetic and long-form segmented rendering; A/V drift and codec/container validation.
- Bitemporal stores: valid time vs transaction time; graph provenance and uncertainty; HDC XOR/multiplication distinction for binary/bipolar encodings.
- Multi-agent graphs, queue stability, Nash mechanisms only if actually useful; do not confuse theory of games with operating-system scheduler guarantees.
- Formal verification using Lean/Coq/Z3/SMT for bounded invariants; characterize what is not proven.
- Bayesian experimental design and causal inference where relevant; statistical significance, test contamination, multiple comparisons.
- Landauer bound clearly described as a theoretical physical limit, not a practical Android thermal-management algorithm.
- Cain's Jawbone permutation/constraint search and reproducible ranking of candidates; never call a heuristic ordering a mathematical proof.
- Failure cost of distributed transactions, secure media pipelines and entitlement accounting; all assumptions auditable.

## 5. Continuous GitHub engineering / DGM-RSI

Define a **real deployable** continuous worker with GitHub App installation-scoped credentials, webhook auth or scheduled polling, bounded queue, idempotent job claims, repo snapshots pinned by SHA, AST analysis, sandboxed multi-language compilation, tests, model-generated candidate patches, independent code review, license/security checks, immutable provenance, staged rollout, review gates, CAS branch update and rollback. Use `main` only per repository instruction; feature changes awaiting approval should be represented as patch artifacts and checks, not hidden unauthorized direct commits. Explicitly show how an authorized human can approve promotion.

State capabilities precisely: can inspect and propose edits in any repo with granted permissions, not magically write to all GitHub. No access tokens in repository or chat. Provide tested Rust, Flutter, Python, C++ examples, launch manifests and monitoring dashboards. If no runtime service is deployed, never say the agent "works 24/7".

## 6. Required deliverables, in enforced order

A. Full source inventory: every PDF/DOCX page and user requirement; exact citations, corrected OCR/code transcription, originality/IP and confidence audit.
B. `requirements/traceability.csv` with at least 339 preserved IDs + extras; requirements dependency graph and gap matrix.
C. Comparable competitor capability study: Google Flow, Picsart, relevant Music AI apps, Pinokio, image/video model managers, agent builders; supported features only, reproducible citations.
D. Versioned reference architecture: ADRs, C4 deployment diagrams, per-module API and data contracts, threat model, hybrid cloud cost and redundancy.
E. Mathematical research report with formal derivations, proofs or **explicit unproven claims**, benchmark plans and test fixtures.
F. Completely enumerated, actual repository directory/file tree with a responsible module/contract for each file.
G. Implementation file-by-file, prioritized in dependency order: real syntactically valid code and tests; no filler, no `TODO` presented as a working feature; include lockfiles, configs, packaging and licenses.
H. Flutter Android APK/AAB signed in authorized CI (when signing credentials are securely present), smoke testing on real devices, accessibility and all UI assets/slots, plus server infrastructure.
I. Running independently hosted GitHub engineering agent with real telemetry, deploy proofs and rollbacks, if infra is authorized; otherwise deployment instructions and **BLOCKED** ledger.
J. Detailed financial plan, tier matrix, payment adapters, legal/app-store compliance, GPU cost accounting, seller marketplace and sponsor/affiliate policy.
K. Periodic update to README top roadmap and each requirement state with actual commit SHA, test run ID, measured result and rationale.

**Stop condition:** never label a feature complete unless its acceptance test actually passed and evidence is linked. If the output does not fit one response, emit coherent numbered deliverable files; persist progress in the repository and continue by next queued task. Do not discard later modules. Record all genuine blockers and explicitly distinguish "specified" from "implemented", "tested" and "deployed".
