# Web Studio — Android UI and artifact contracts

User requested **three functional modules in Unthinkable AI**: Web Scraper, API Wrapper Creator and Website Creator NoCode, to be integrated under the WEB domain. This is separate from the final branded UI/screens/assets the owner will supply later.

## Implemented Android
- `lib/features/web_studio/web_studio_screen.dart`: 3-tab screen, dark/purple styling, no copyrighted reference imagery; optional server HTTPS and ephemeral API key, restricted page inspection, structured results, offline endpoint contract editing/export and offline block-based website editor with mobile preview.
- `lib/features/web_studio/web_studio_api.dart`: authenticated HTTPS calls to FastAPI; no stored server key.
- `lib/features/web_studio/nocode_engine.dart`: static responsive HTML/CSS export, escaped content, Content Security Policy, restricted button links; local saved drafts through `shared_preferences`.
- `test/web_studio_test.dart`: unit and widget tests for generated HTML, wrapper OpenAPI, HTTP request validation and saved website drafts.

## Backend
- `services/web_studio/scraper.py`: inspect HTML and opt-in allowlisted HTTPS fetch (public IP only, pinned TLS IP, robots.txt, document limit, no redirects).
- `services/web_studio/wrapper.py`: Pydantic-validated OpenAPI description of manually defined operations; **no automatic reverse proxy or credential capture**.
- `services/web_studio/nocode.py`: server-side HTML and ZIP generator; returns page HTML and archive encoded in response.
- `services/web_studio/router.py`: authenticated API endpoints; docs at `services/web_studio/README.md`.

## Still required for complete source-domain vision
- Asset manager and reference design import (graphics will be provided separately).
- Browser-based JavaScript rendering with sandbox, CSS/image/link asset download, user-approved source capture and rights review.
- Editable multi-page app/site project with navigation and content storage, visual drag/drop layout engine, accessibility audit, SEO, built-in preview webview, responsive templates and theme tokens.
- CMS importers, forms/email and database persistence, deployment to connected hosting and verified DNS/domain management.
- Typed client SDK build & private proxy only for explicitly configured/authorized upstream services. Real backend/database replication requires owner-provided credentials and export access.

Never claim the HTML inspector has copied hidden API logic or a private database.
