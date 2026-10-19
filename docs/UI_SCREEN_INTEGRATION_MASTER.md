# UNTHINKABLE AI — MASTER UI SCREEN & INTEGRATION INVENTORY
**Version:** 2026-10-19 · **Source:** current `main` at time of review; 339 tracked base requirements / 27 source domains, user-supplied Website Cloner report and additional user directives.

**Audience:** UI/UX designer preparing all screens before final visual asset handoff. This is a **navigation / interaction contract**, not a claim that every screen is coded. No missing-feature cards are allowed to masquerade as working functions.

## Status legend
- **UI+API** — tested Flutter entry/screen and a related usable API/local engine. External deployment or end-to-end provider integration can still be missing.
- **UI** — Flutter/local prototype has concrete editing/storage/output. No full provider/native engine.
- **API** — backend endpoint/CLI exists, but first-party screen may not be directly integrated.
- **Prototype** — interface/registry or planning operation, with final engine absent.
- **Planned** — proposed screen, not yet implemented.
- **OPTION** — surfaced from reference materials only; user selection required before becoming committed product scope.

Every screen should have: loading, empty, ready, progress, completed, error, offline, denied-permission, insufficient-resources, canceled, review-required and unavailable-engine states where relevant. Do not design a success state that the backend cannot substantiate. All network actions must show which provider, potential costs and explicit user consent.

## Primary navigation
- Start / Command Search, Chat & Models, Creative Studio, Build & Code, Web & Research, Communications, Marketplace, Owner Workspace, Account & Settings.
- Website Studio has **two existing Flutter paths**, one at `lib/features/web/` (authorized site import, multi-page NoCode editor), the other at `lib/features/web_studio/` (direct HTML inspector, OpenAPI builder, quick page NoCode). Preserve both for now, use one design system, then converge services after regression testing.
- Studio generator cards must have separate *native engine unavailable* and *provider not configured* states, rather than advertising unsupported generation.

## Website Studio — detailed UI handoff
This is the 16-page website cloning document transformed into a buildable authorized Web Studio UX. `P` means future integration, not an already-running plugin. HTML analysis is not private backend extraction.

| ID | Screen / panel | User inputs, outputs, controls | Integrations / required evidence | State |
|---|---|---|---|---|
| WEB-01 | Web Studio Dashboard | Projects, recent jobs, recent scans, create/open, connection state | Flutter two implementations; gateway capabilities | UI |
| WEB-02 | New website / project | Name, website category, source: blank/template/import, project location | NoCode project schemas; local preferences | UI |
| WEB-03 | Connect backend | User-supplied HTTPS root, ephemeral API key, connectivity check, permission status | FastAPI gateway Bearer; no persisted secret | UI+API |
| WEB-04 | Source permission & scope | Domain ownership/authorization confirmation, robots policy, allowlist details, pages cap | WEB_SCRAPER_ALLOWED_HOSTS / WEB_STUDIO_ALLOWED_HOSTS | UI+API |
| WEB-05 | Scrape URL | HTTPS source URL, scan button, progress/errors, number of pages | /api/web/scrape and /api/web-studio/scraper/fetch | UI+API |
| WEB-06 | Paste HTML | HTML editor/clipboard input, inspect and report | /api/web/extract and /api/web-studio/scraper/inspect | UI+API |
| WEB-07 | Crawl job history | Saved job IDs, timestamps, state, resume/cancel, errors | Durable worker job queue/storage | Planned |
| WEB-08 | Sitemap / Page discovery | Pages visited, internal links, hierarchy, broken links | Allowlisted limited crawler; expand with budget | API |
| WEB-09 | DOM Structure Inspector | Headings, semantic nodes, links, forms count, sanitized element tree | Current safe HTMLParser, future DOM renderer | API |
| WEB-10 | Content Inventory | Paragraphs, title/meta, image/link lists, extraction approval | Current parser; excludes credentials and form values | UI+API |
| WEB-11 | CSS & Design Tokens Extractor | Fonts, colors, spacing, layout/grid, component inventory | Authorized asset/CSS parsing | Planned |
| WEB-12 | Asset Browser | Images/icons/fonts, license and source metadata, choose to import | Rights review + secured object storage | Planned |
| WEB-13 | Render JavaScript / SPA | Sandbox worker config, wait strategy, DOM snapshot, screenshot | Playwright/Puppeteer worker; not yet connected | Planned |
| WEB-14 | Visual Comparison | Source-versus-rebuilt side-by-side, viewport sizes, difference report | Browser screenshot worker / image diff | Planned |
| WEB-15 | Network HAR / API Map | Owner-supplied HAR import, redact tokens, discovered endpoints, request schemas | Authorized HAR/Postman import; no interception of third parties | Planned |
| WEB-16 | SEO Inspector | Meta titles, descriptions, headings, canonical, schema.org, sitemap | SEO audit engine and crawling | Planned |
| WEB-17 | Accessibility Inspector | Contrast, keyboard navigation, alt-text, WCAG issues | axe-core/browser tests | Planned |
| WEB-18 | Performance / Audit | Core Web Vitals, network waterfall, bundle weight, remedies | Lighthouse/Playwright isolated workers | Planned |
| WEB-19 | Site snapshot / handoff | Versioned snapshot, tracked source, copy JSON, import to builder | /api/web/wrapper; snapshot storage | UI+API |
| WEB-20 | API Wrapper Wizard | Owned API name, version, operation ID, GET/POST/etc, paths, summary | OpenAPI 3.1 generator; strict validation | UI+API |
| WEB-21 | OpenAPI Preview & Export | JSON contract, endpoints, validation warnings, copy/export | /api/web-studio/wrapper/build + local Dart builder | UI+API |
| WEB-22 | SDK / typed client generator | Target Dart/TypeScript/Python/Rust, generated client, download | OpenAPI generators in isolated worker | Planned |
| WEB-23 | Authorized API Proxy Builder | Select upstream owned API, scoped auth, headers, timeout, proxy test | Authenticated backend proxy + rate limit, secrets manager | Planned |
| WEB-24 | API Credentials & Permissions | Credential aliases, per-provider grants, revoke, audit receipts | Vault/Keystore/secret manager, tenant auth | Planned |
| WEB-25 | Import scanned site to editor | Select snapshot, map pages, review content, editable draft | /api/web/nocode/import-snapshot | UI+API |
| WEB-26 | NoCode Templates | Light, Midnight, Gold, previews, create from template | /api/web/nocode/templates; page editor | UI+API |
| WEB-27 | NoCode Pages & Navigation | Create/rename/reorder max schema pages, slugs, hierarchy | lib/features/web/website_project.dart | UI |
| WEB-28 | NoCode Sections / Blocks | Hero, text, features, CTA, contact, add/edit/delete/reorder | Multi-page WebsiteCreatorScreen and quick builder | UI |
| WEB-29 | NoCode Drag & Drop Canvas | Touch reorder, snapping, spacing, visual tree, undo/redo | Dedicated visual layout engine | Planned |
| WEB-30 | Theme / Styles | Dark/light/gold accents, typography, colors, spacing | Current themes; expanded design-token system | UI |
| WEB-31 | Responsive Preview | Phone/tablet/desktop breakpoints, device rotation, viewport rulers | Current mobile preview; true WebView/headless browser later | UI |
| WEB-32 | Content & Media Editor | Images/backgrounds, alt text, consent, media upload, icon/font picker | Asset manager, user-supplied artworks | Planned |
| WEB-33 | Forms & Data Sources | Form builder, validation, destinations, spam checks, storage | Real backend/database connectors, CRM, email | Planned |
| WEB-34 | Per-page SEO / Accessibility | Meta/canonical/OG, contrast and keyboard checklist | SEO + accessibility validators | Planned |
| WEB-35 | Project History & Versions | Saved drafts, autosave, version comparison, undo/rollback | Current local save; versioned persistence needed | Planned |
| WEB-36 | Code / HTML Preview | Escaped generated HTML/CSS, copy, inspect, static output | NoCode local renderer; restricted CSP | UI |
| WEB-37 | Export HTML / ZIP / JSON | Select pages and file type, archive contents, share/download | Current HTML/ZIP/JSON exporters (various paths) | UI+API |
| WEB-38 | CMS Import / Export | WordPress and other source export, content fields, media mapping | Official CMS APIs/exports with owner login | Planned |
| WEB-39 | Authorized Backend / DB Migration | Export owner-owned DB schema/data, mapping, checksum, restore drill | SSH/Rsync, pg_dump/mysqldump, encrypted grants | Planned |
| WEB-40 | Publish / Hosting | Choose verified hosting, preview URL, deploy, rollback | Netlify/Vercel/Cloudflare/owned server adapter | Planned |
| WEB-41 | Domains, DNS & TLS | Domain verification, records, certificate status, HTTPS policy | Registrar/DNS/ACME provider integration | Planned |
| WEB-42 | Security Scan & Release Gate | CSP, secret scans, malicious scripts, permission proof, approval | Browser audit, SAST, deploy policy | Planned |
| WEB-43 | Monitoring & Backups | Uptime, logs, analytics consent, restore snapshot, incidents | Monitoring/backup workers and cloud object store | Planned |
| WEB-44 | Job Batch & Worker Controls | Concurrency, crawl budget, rate, worker health, stop/kill | Worker queues; proposed Node Worker Threads | Planned |

## Full product screens — grouped by 27 requirement domains

### FOUND — Start & Identity

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| FOUND-UI-01 | Command dashboard / global search | Find and open 27 domains, pinned actions | UI |
| FOUND-UI-02 | First-run onboarding & sign-in | Identity, age/terms, permissions, plan, import assets | Planned |
| FOUND-UI-03 | Brand splash & 8-second Santa Muerte intro | Animated intro; user-supplied visuals/phrases | Planned |
| FOUND-UI-04 | Theme, languages, accessibility | PL-first i18n, dark/gold, font/contrast, motion settings | Prototype |
| FOUND-UI-05 | Account, devices & privacy center | Sessions, storage, data export, consent | Planned |

### MODELS — Models & Runtime

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| MODELS-UI-01 | Model marketplace / Hugging Face | Search GGUF/safetensors and compare downloads/licensing | Planned |
| MODELS-UI-02 | Model library & import | Pick local files, registry, SHA-256, compatibility checks | UI |
| MODELS-UI-03 | Engine status & hardware capabilities | GPU/NPU/CPU, RAM, battery, native bridge | Prototype |
| MODELS-UI-04 | Dual GGUF target/draft settings | Sampling, speculative decoding, independent caches | Planned |
| MODELS-UI-05 | Provider & API profiles | User keys, routing, quotas, privacy, cost estimates | Prototype |
| MODELS-UI-06 | Local inference console | Run benchmark and real tokens per second | Planned |

### REASON — Reasoning & Memory

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| REASON-UI-01 | Reasoning workspace | Questions, multi-step plans, evidence/output comparison | Planned |
| REASON-UI-02 | Memory graph & RAG libraries | Documents, knowledge links, embeddings, delete/refresh | Planned |
| REASON-UI-03 | Model reasoning evaluation | Test cases, hallucination/accuracy metrics, trace | Planned |
| REASON-UI-04 | Personal knowledge permissions | Who sees sources, revoke/export/forget | Planned |

### AGENTS — Agent Factory

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| AGENTS-UI-01 | Agent Builder NoCode | Name, role, model, tools, workflows, memory, publish | Planned |
| AGENTS-UI-02 | Agent Builder Code | Source, Rust/Zenoh/tools integration, tests | Planned |
| AGENTS-UI-03 | Agent/team/swarm orchestrator | Multiagent roster, messages, delegation, limits | Prototype |
| AGENTS-UI-04 | Agent runs & event stream | Jobs, logs, pause, approval, replay | Planned |
| AGENTS-UI-05 | Agent evaluation & certification | Evidence, benchmarks, policy, certificate records | Planned |

### EXT — Tools/Skills/MCP

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| EXT-UI-01 | Plugin & Skills catalog | Browse, install, permissions, ratings | Planned |
| EXT-UI-02 | Tool/Skill Creator Code + NoCode | Inputs, schema, version, tests, export | Planned |
| EXT-UI-03 | MCP/OMAs adapters | Server catalog, protocol routes, tool grants | Planned |
| EXT-UI-04 | Extension sandbox & permission audit | Caps, network grants, usage, revoke | Planned |

### DEEP — Research

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| DEEP-UI-01 | Deep Research workspace | Question, scope, sources, reasoning budget | Planned |
| DEEP-UI-02 | Search results & source audit | Citations, confidence, version, exclusions | Planned |
| DEEP-UI-03 | Experiment lab | Reproducible runs, datasets, hypotheses, results | Planned |
| DEEP-UI-04 | Report & bibliography editor | Evidence tree, export MD/PDF, unresolved facts | Planned |

### DGM — Governed Self-improvement

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| DGM-UI-01 | Change proposal queue | Suggested patch, diff, impact, origin, owner | Planned |
| DGM-UI-02 | CI/bench validation | Tests, metrics, security findings, artifacts | Planned |
| DGM-UI-03 | Review, release & rollback | Explicit approval, signed updates, revert | Planned |
| DGM-UI-04 | Evolution history | Changesets, evaluator scores, regression timeline | Planned |

### GITHUB — Engineering Workspace

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| GITHUB-UI-01 | Repository explorer | Files, branches/read-only source views, issues | Planned |
| GITHUB-UI-02 | Code editor/IDE | Multi-language editing, lint, local diffs | Planned |
| GITHUB-UI-03 | Pull/change review | Patches, tests, approval, signed commit gates | Planned |
| GITHUB-UI-04 | CI monitor | GitHub Actions runs, failures, logs, artifact links | API |
| GITHUB-UI-05 | Repository reuse audit | 633 discovered repos: license/code/tests review | API |

### IMAGE — Images

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| IMAGE-UI-01 | Image AI generator | Prompt, model, aspect, seed, batch, cost | Prototype |
| IMAGE-UI-02 | ODYN model picker | Models, checksum, native engine availability | UI |
| IMAGE-UI-03 | Image-to-image & masking | Reference photo, mask, inpaint, outpaint | Planned |
| IMAGE-UI-04 | Face replacement (authorized) | Consent, identities, before/after, export | Planned |
| IMAGE-UI-05 | Background remover | Foreground masks, alpha/PNG export | Planned |
| IMAGE-UI-06 | Advanced image editor | Layers, history, retouch, upscale, style | Planned |

### VIDEO — Video & NLE

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| VIDEO-UI-01 | Film project dashboard | Create/open, runtime, deliverables, crew | UI |
| VIDEO-UI-02 | Storyboard & master prompts | Shots, descriptions, references, duration, approval | UI |
| VIDEO-UI-03 | 18-role film crew planner | Crew tasks, role assignments, state | API |
| VIDEO-UI-04 | Film production API planner | Send timeline HTTPS, verify server returned plan | UI+API |
| VIDEO-UI-05 | Video AI / shot generator | Wan/Seedance/Kling/Veo providers by capability | Planned |
| VIDEO-UI-06 | Nonlinear timeline & tracks | Video, audio, transitions, effects, 123+ minute assemblies | Planned |
| VIDEO-UI-07 | Actor & continuity library | Identity references, scene continuity, casting | Planned |
| VIDEO-UI-08 | Matting/face swap | Mask video, identity permission, render | Planned |
| VIDEO-UI-09 | Long-form render queue | Segment, resume, concat, captions, quality audit | Planned |

### AUDIO — Audio, Voices, Music

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| AUDIO-UI-01 | Music creation | Instrumental, lyrics, style, license and stems | Planned |
| AUDIO-UI-02 | Music-video creator | Song upload, beat analysis, storyboard/clip timing | Prototype |
| AUDIO-UI-03 | Video audio extraction | Import video, select audio track/format | Planned |
| AUDIO-UI-04 | Voice cloning | Consent, enrollment, language, voice preset | Planned |
| AUDIO-UI-05 | Speech-to-text / TTS | Transcribe, synthesize, speaker controls | Planned |
| AUDIO-UI-06 | Audio mixing & mastering | Multi-track, waveform, export | Planned |

### GAME — Game Builder

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| GAME-UI-01 | Game project templates | 2D/3D, genre, engine selection, scope | Planned |
| GAME-UI-02 | Game Builder NoCode | Entities, scenes, behaviours, assets, interactions | Planned |
| GAME-UI-03 | Game Code IDE | Rust/C++/C#/GDScript editor + build logs | Planned |
| GAME-UI-04 | World/level editor | Scenes, collisions, physics, actors | Planned |
| GAME-UI-05 | Unity/Godot/Unreal connectors | Editor-specific MCP integration and exports | Planned |
| GAME-UI-06 | Build, test and release | Android/desktop packages, QA and publishing | Planned |

### APPS — App Builder & IDE

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| APPS-UI-01 | App Builder NoCode | Screen templates, data entities, flows, forms | Planned |
| APPS-UI-02 | App Builder Code | Framework, live code editing, dependencies | Planned |
| APPS-UI-03 | IDE & tests | Terminal, build errors, lint, previews | Planned |
| APPS-UI-04 | Mobile build factory | APK/AAB/iOS/desktop targets, signing | Planned |
| APPS-UI-05 | 33 application + 33 tool categories | Templates catalogue derived from source specifications | Planned |

### PUBLISH — Publishing Studio

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| PUBLISH-UI-01 | Book/ebook builder | Chapters, covers, pagination, EPUB/PDF | Planned |
| PUBLISH-UI-02 | Audiobook producer | Narrators, pronunciation, timeline, export | Planned |
| PUBLISH-UI-03 | Illustrated kids book | Character sheets, spread layout, parental safeguards | Planned |
| PUBLISH-UI-04 | Comic/manga studio | Panels, scripts, lettering, character continuity | Planned |
| PUBLISH-UI-05 | Roleplay/story writer | Worlds, chapters, branching decisions | Planned |

### CHAT — Chat, Rooms, Phone

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| CHAT-UI-01 | General AI chat | Provider choice, conversation, streaming, prompt history | UI |
| CHAT-UI-02 | Voice & realtime chat | Mic, speaker, live transcript, interrupt | Planned |
| CHAT-UI-03 | QR one-time encrypted rooms | Create, join, share QR/link, destroy keys/room | Planned |
| CHAT-UI-04 | Virtual Number VIP generator | Prefix, length, rank, choose/save internal alias | UI+API |
| CHAT-UI-05 | Internal alias claims | Claim/release/TTL and collisions, tenant scope | API |
| CHAT-UI-06 | Public DID inventory | Verified operator offers, availability, purchase | Planned |
| CHAT-UI-07 | VoIP dialer/SIP/WebRTC | Calls, caller-ID grants, media routing | Planned |
| CHAT-UI-08 | SMS/MMS & alias email | Message inbox, routing, verified senders | Planned |

### BROWSER — Browsers & Authorized OSINT

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| BROWSER-UI-01 | Clearnet browser | Tabs, saved pages, downloads and controls | Planned |
| BROWSER-UI-02 | Separate Tor browser/profile | Isolation, password, bridges, leak warnings | Planned |
| BROWSER-UI-03 | Authorized OSINT workspace | Public-data searches, notes, legal scope | Planned |
| BROWSER-UI-04 | Scraper & site inspector | Authorized HTTPS site extraction, reports | UI+API |
| BROWSER-UI-05 | Web permissions, cookies & sessions | Per-site consent and privacy settings | Planned |

### ANDROID — Device Guardian

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| ANDROID-UI-01 | Hardware status | Battery, memory, storage, CPU thermal metrics | Planned |
| ANDROID-UI-02 | Permission dashboard | Apps/Android grants, notifications, revoke | Planned |
| ANDROID-UI-03 | Storage & device diagnostics | Files, cache, reports, troubleshooting | Planned |
| ANDROID-UI-04 | Mobile engineering controls | Android build/dev tools with explicit permissions | Planned |

### WEB — Web & Site Studio

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| WEB-UI-01 | Web Engineering Studio | Entry for Scraper/Wrapper/NoCode routes | UI |
| WEB-UI-02 | Website Scanner & Cloner | Owned site scan, snapshot map, import to editor | UI+API |
| WEB-UI-03 | NoCode Website Creator | Single/multi-page sections, templates, saved draft | UI+API |
| WEB-UI-04 | API Wrapper/OpenAPI builder | Manual API contract and JSON export | UI+API |
| WEB-UI-05 | Website Hosting / Domains / CMS | Provider connect, deploy, DNS, import | Planned |
| WEB-UI-06 | Email aliases & Google Workspace | Alias provisioning and admin consent | Planned |
| WEB-UI-07 | Promo, discounts & landing pages | Templates, affiliate disclosure and campaigns | Planned |

### OWNER — Owner-only Workspace

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| OWNER-UI-01 | Owner authentication | Independent vault key, biometrics, device trust | Planned |
| OWNER-UI-02 | Secret vault & source storage | Encrypted assets, scoped secrets, file references | Planned |
| OWNER-UI-03 | SFTP/FTP/SMB clients | File transfers and permission log | Planned |
| OWNER-UI-04 | Google Drive & DB sandbox | Connected sources, queries, access receipts | Planned |
| OWNER-UI-05 | Private mathematics research hub | Segregated owner-only research and logs | Planned |

### MATH — Millennium & Cain

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| MATH-UI-01 | Math research console | Problem statements, theorem/proof notebooks | Planned |
| MATH-UI-02 | Formal solver & verification | Lean/Coq/Z3, exact assumptions and certificates | Planned |
| MATH-UI-03 | Cain's Jawbone workspace | Page cards, order constraints, ranking, uncertainty | API |
| MATH-UI-04 | Evidence & proof audit | Reproducible runs, accepted/rejected reasoning | Planned |

### MARKET — Marketplace

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| MARKET-UI-01 | Marketplace browse/search | Agents, tools, prompts, sites, products | Planned |
| MARKET-UI-02 | Product detail & license | Version, permissions, seller, cost | Planned |
| MARKET-UI-03 | Creator/seller workspace | New listing, file upload, pricing, review | Planned |
| MARKET-UI-04 | Install/rent/license management | Entitlements, update history, revoke | Planned |

### PAY — Billing & Monetization

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| PAY-UI-01 | Plans comparison | Free through paid, feature entitlements and quotas | Planned |
| PAY-UI-02 | Payment checkout | PayPal/BLIK/Revolut/crypto only where permitted/verified | Planned |
| PAY-UI-03 | Subscription dashboard | Invoices, renewal, cancellation, refunds | Planned |
| PAY-UI-04 | Affiliate/ads transparency | Sponsored disclosures, prefs, opt-out | Planned |
| PAY-UI-05 | Cost and compute budget | Token/GPU usage, hard spend limits | Planned |

### INFRA — Cloud & Ops

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| INFRA-UI-01 | Infrastructure overview | IBM/Oracle/other compute, quotas, uptime | Planned |
| INFRA-UI-02 | Deployment targets | Workers, containers, queues, secrets and cost | Planned |
| INFRA-UI-03 | Security/audit log | Grants, incidents, job receipts, alerts | Planned |
| INFRA-UI-04 | Disaster recovery | Backups, restore drills, error budget, SLO | Planned |

### FORMAL — Formal Computing

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| FORMAL-UI-01 | Proof workbench | Definitions, constraints, solver selection | Planned |
| FORMAL-UI-02 | Benchmark lab | Latency/accuracy/energy profiles, reproducibility | Planned |
| FORMAL-UI-03 | Simulation and optimization | Cases, parameters, traces, comparisons | Planned |
| FORMAL-UI-04 | Formal review reports | Certified/uncertified results, failed assumptions | Planned |

### LEGAL — Safety & Privacy

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| LEGAL-UI-01 | Privacy & consent center | Data controls, telemetry, permissions | Planned |
| LEGAL-UI-02 | Attribution/licensing | Model licenses, source images, third-party code | Planned |
| LEGAL-UI-03 | Abuse and content protections | Consent and authorization for identity media/telephony | Planned |
| LEGAL-UI-04 | Compliance/audit evidence | Notices, retention, disputes, incident history | Planned |

### OPTION — Optional capabilities only

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| OPTION-UI-01 | Discovery and approval of optional domains | Review VR/AR, hardware, other report-only modules | OPTION |
| OPTION-UI-02 | Optional feature compatibility | Dependency/runtime/privacy feasibility | OPTION |
| OPTION-UI-03 | Enablement decision log | Owner explicitly includes/excludes optional features | OPTION |

### REUSE — Repository Audit & Reuse

| UI ID | Screen | Main controls / behavior | Status |
|---|---|---|---|
| REUSE-UI-01 | Projects discovered | Search/filter source repo inventory (633 names, not 633 audited) | API |
| REUSE-UI-02 | License and trust review | Licenses, activity, source code, test evidence | API |
| REUSE-UI-03 | Import plan + provenance | Version pinning, copy policy, dependency report | Planned |
| REUSE-UI-04 | Regression integration dashboard | Tests and rollout per imported component | Planned |
## Global integration connectors (plan by card or settings panel)
| Connector group | Proposed integrations / capabilities | Real status today |
|---|---|---|
| Web capture | HTTrack, Wget, Playwright, Puppeteer, Cheerio | Document proposals. Current implementation uses controlled Python parsers/fetchers; no integrated browser renderer |
| API capture & specification | Owner HAR/Postman exports, OpenAPI 3.1, Burp/mitmproxy for explicit authorized audits | OpenAPI generation and snapshot wrapper implemented; traffic capture and proxy not implemented |
| Site migration | SSH, Rsync, Docker, Terraform, pg_dump, mysqldump | Document proposal only; requires owner-provided access |
| CMS & publish | WordPress, hosting (Vercel/Netlify/Cloudflare/etc), DNS, ACME | Not connected |
| Media models | GGUF, Hugging Face, ODYN, various SD and video/audio families | Import registry/chat API are prototypes; GPU inference is not in current Android APK |
| Game engines | Godot, Unity, Unreal, MCP bridges | Not integrated or benchmarked |
| Payments | PSP/provider account authorizations, billing/webhooks, Google Play controls | Not implemented |
| Telecom | DID/VoIP operator, SIP/WebRTC, Kamailio/FreeSWITCH, SMS/SMPP | Internal aliases exist, no carrier |
| Clouds | IBM/Oracle/third-party managed compute | No live production deployment established here |
| Source and storage | GitHub, GitLab, Google Drive, SMB, SFTP, encrypted app vault | GitHub CI monitor/source audit exists; owner workspace integration missing |

## Designer deliverables and asset slots
1. Supply mobile-first **navigation frames** for all main areas (portrait Android), tablet adaptations and bottom navigation/sidebar.
2. For each Web Studio screen WEB-01..WEB-44 design **empty / loading / ready / error / permission denied / limit exceeded / backend not connected**. Advanced missing engines have an honest `Install/Connect` state, never a fake `Done`.
3. Studio popular tools artwork names already specified in `docs/AI_TOOL_ARTWORK_SLOTS.md`: `video_generator`, `music_video`, `video_face_swap`, `video_matting`, `viral_music`, `animals_video`, `ai_image`, `image_face_swap`, `background_remove`, `audio_extract`, `voice_clone`. Suggested WEBP 1200×700, with safe caption area. Provide optional hero artwork for `virtual_number`, `scraper`, `api_wrapper`, `nocode_creator`, `website_cloner`, `film_studio`, `model_library`, `main_dashboard`.
4. Product theme: deep OLED black, 24k-gold primary highlights, optional restrained violet accent for editor sub-navigation, own Santa Muerte/Unthinkable AI branding; PL default, inclusive accessible text, no third-party image copying.
5. Editor route diagrams: (A) source permission → scan → structure review → snapshot/wrapper → editable site → preview/export; (B) template → multi-page editor → export → connected publishing (future); (C) manually define API operations → validate OpenAPI → optional owned-provider adapter (future).
6. Do not imply production support where only a scaffold exists. In the final mockups, differentiate **Ready**, **Prototype**, **Connect engine**, **Coming later**, **Owner-only**.

## Acceptance and gaps
- The complete product requirement register is `requirements/requirements.csv` (339 IDs / 27 domains); this file maps screen groups but **does not yet assign each individual requirement ID to a specific screen**. Maintain a separate formal 339-to-screen matrix during the implementation audit.
- Website source PDF is a **reference design**; copying server databases without privileged owner access is not technically established. Public page analysis and consented migration are separate workflows.
- As of 2026-10-19, Android GitHub Actions run [39257970067](https://github.com/mojealterego/Unthinkable-AI-/actions/runs/39257970067) succeeded for current main at initial inventory review. This does not certify production readiness of each feature.
- Every planned external connector requires capability verification, licensing, secrets/scopes, cost estimates and runnable acceptance tests. No hidden side-effect, no unauthorized service access.
