# Website Studio — source provenance, scope and boundaries

Reference: user-supplied **Klonowanie Stron Internetowych_ Frontend, Backend, Baza Danych.PDF** (16 pages). It covers static web mirroring (HTTrack/Wget), Puppeteer/Playwright SPA rendering, Cheerio parsing, authorized HAR/API investigation, SSH/Rsync, Docker/Terraform, database dump/migration, JWT/security audits and Node.js worker-thread scans. These are **reference tool proposals** and must not be confused with implemented components.

## Implemented in this repository

| Workflow | What actually runs |
|---|---|
| Public HTML structure extraction | Python HTMLParser, title/meta, headings, links, image URL/alt, form count; excludes input values, scripts and secrets |
| Remote website scraper | HTTPS-only, exact administrator allowlist, explicit ownership flag, DNS global-IP inspection, direct IP-pinned TLS, robots.txt, no redirects, no proxies, no credentials, 1–5 pages, 1.5 MB per response |
| Read-only API wrapper | Turns approved HTML-derived facts into versioned JSON suitable for the NoCode editor; never proxies arbitrary authenticated APIs |
| NoCode builder | Versioned site/pages/sections schema, validated themes, hero/text/features/CTA/contact, escaped HTML, responsive CSS, static navigation |
| NoCode export | Preview endpoint with restrictive CSP, ZIP with HTML pages + editable `site.json` + readme |
| Import from wrapper | Converts a structured website snapshot into an **editable draft**, not a direct pixel-identical clone |

**Backend endpoints** under `/api/web`:
- `GET /capabilities`
- `POST /extract` — user-supplied HTML
- `POST /scrape` — authorized live site
- `POST /wrapper` — normalized snapshot mapping
- `GET /nocode/templates`
- `POST /nocode/preview`
- `POST /nocode/export`
- `POST /nocode/import-snapshot`

All endpoints require the configured `API_KEY` (no API key => fail-closed). The live scraper requires `WEB_SCRAPER_ALLOWED_HOSTS=your-owned-domain.example` and explicit acknowledgment; HTTPS client does not trust arbitrary hosts, redirects, cookies, proxies, private IPs or host-mismatched certificates. For production also enforce network egress rules, DNS policy, bandwidth/rate limits, legal ownership and persistent audit. This is not a complete Playwright/Puppeteer SPA renderer, a full HAR/traffic interception layer, or a database migration agent; those require separate isolated workers and authenticated infrastructure.

## UI dependency

The user will provide the final visual design. Existing backend and schema make it possible to build an independent NoCode website editor with form-based editing of pages/sections. User-provided graphic assets can be connected later; **no copyrighted imagery from third-party sites has been copied**.

## Security improvements relative to the PDF examples

The PDF shows `--no-sandbox`, `--disable-web-security`, `robots=off` and logs decoded JWT claims; these patterns are deliberately **not** used. HTML snapshots do not include private secrets, credentials, form input values or session cookies. JWT tokens are not extracted or printed. Output HTML is escaped and free of executable JavaScript; generated pages are not auto-deployed or hosted.
