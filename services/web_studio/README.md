# Website Cloner / Web Scraper / API Wrapper / Website NoCode

## Actual implemented capabilities
- \`POST /api/web-studio/scraper/inspect\` parses caller-provided HTML without executing JavaScript, extracting bounded page structure (headings, paragraphs, links, images, forms count). No credentials, session cookies or hidden endpoints are extracted.
- \`POST /api/web-studio/scraper/fetch\` fetches **only explicitly administrator-allowlisted HTTPS sites** on port 443. This is a live, read-only scraper, NOT a universal website clone. It validates DNS addresses are public, pins the validated address for the TLS connection, disables redirects and cookies, consults robots.txt, checks MIME, limits document bytes/timeouts.
- \`POST /api/web-studio/wrapper/build\` builds OpenAPI 3.1 contract JSON from human-defined operations, validates routes and identifiers, and rejects duplicates. This does not discover or call a private backend.
- \`POST /api/web-studio/nocode/render\` creates escaped, responsive, standalone HTML/CSS and downloadable ZIP (base64-encoded) with \`index.html\` and a reversible \`site.json\` description. It never embeds user JavaScript, deploys or connects databases.
- \`GET /api/web-studio/capabilities\` describes actual capabilities. All endpoints require the gateway's \`API_KEY\` Bearer header.

## Deployment
Server: \`services/gateway/Dockerfile\` and \`services/gateway/DEPLOY.md\`.
To allow fetching a site **you own or have express permission to inspect**, configure an exact hostname, e.g. \`WEB_STUDIO_ALLOWED_HOSTS=example.org\`. No wildcards are accepted, no default domains are allowed, and no public DNS is considered by itself to convey consent. The fetching server must have outbound HTTPS/DNS access to the approved host, and should be network-isolated and rate limited.

## Integration boundaries
The source 16-page document describes Puppeteer/Cheerio, HTTP traffic analysis, static scanning and JWT parsing but contains examples that risk logging raw credentials or treating visible tokens as server access. Those are **not** integrated. Decryption or decoding of unrelated website session material is not a valid method to obtain database or server migration access. Database migration requires privileged access supplied by the rightful site owner. JavaScript-rendered SPA capture, visual screenshots, CMS import/export, publishing, advanced page builder and real reverse proxy are future separate capabilities, **not falsely marked as delivered**.

## Planned Android screens
1. Web Studio home / projects
2. Scraper: authorized URL, HTML inspection and extracted structure
3. Wrapper: define endpoints, view/copy OpenAPI
4. NoCode Creator: editable page blocks, themes, live in-app preview, HTML export
5. Assets & website deploy: awaiting user assets and hosting connection

No images have been generated; the owner will supply final art.
