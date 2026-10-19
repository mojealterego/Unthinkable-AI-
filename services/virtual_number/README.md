# Virtual Number — All Virtual Phone integration (stage A)

**Input documents:** user-provided `All_Virtual_Phone_VoIP_Advanced_Architecture_261018_221422.pdf` (2 pages), `All_Virtual_Phone_VoIP_Architecture_261018_221439.pdf` (2 pages), `Projekt Aplikacji All Virtual Phone.pdf` (48 pages).

The first two reference PDFs describe SIP/VoIP, Vanity Generator, ENUM/Redis, Kamailio/FreeSWITCH and Kannel/SMPP. The 48-page report explicitly distinguishes public E.164 routing via operator-allocated DID from arbitrary on-net aliases. We preserve that distinction rather than implementing arbitrary CLI spoofing or pretending a generated number is available.

## Already implemented
- Pure Python, deterministic **vanity ranking heuristic** (tier PLATINUM/GOLD/SILVER/STANDARD, digit entropy and repetitions).
- Arbitrary numeric prefix, including `000`, `111`, and every digit. No hardcoded `798` prefix.
- Secure-random internal aliases and repeated/pair/sequence candidates, 4–18 digits, uniqueness validation.
- Read-only, Bearer-protected endpoints: `GET /api/virtual-number/capabilities`, `POST /api/virtual-number/score`, `POST /api/virtual-number/suggest`.
- Provider inventory screening helper: never treats a user-generated candidate or valid E.164 syntax as proof of availability.
- Explicit output `scope=on_net_only`, `availability=not_checked`, `publicly_routable=false` for every proposed local identifier.
- Offline unit and HTTP integration tests included in the existing service CI.

## Not implemented / requires carrier integration
- Public DID leasing/provisioning and real-time operator availability, inbound/outbound calls, SIP/RTP/WebRTC, SMS/MMS, CNAM, verified CLI presentation, carrier contracts.
- Kamailio SBC, FreeSWITCH Media, SMPP/Kannel gateway, PostgreSQL migrations, Android TelecomManager/CallsManager bridge, provider-specific DNO checks and legal compliance.
- Secret/tenant scoped identity, operator KYC requirements, rate limits, encrypted CDR retention and abuse detection.

**The generator creates memorable candidates, not functioning telephone numbers.** No headers such as `From`, `P-Asserted-Identity` or arbitrary sender IDs are rewritten. A public number can only be shown as reserved/routable after atomic allocation and caller-ID verification through a real carrier adapter.
