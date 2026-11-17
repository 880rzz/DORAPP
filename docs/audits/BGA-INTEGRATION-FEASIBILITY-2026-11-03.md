# BGA Pályázati Adattár integration feasibility (2026-11-03)

## Sources examined

| Source | URL | Status |
| --- | --- | --- |
| Official map UI | https://adattar.bgazrt.hu/adattar/riport/terkep.xhtml | PARTIAL — interactive JSF/PrimeFaces page loads with browser-like GET; HEAD observed `403`; session cookie `JSESSIONID` issued |
| Government announcement | https://kormany.hu/hirek/atlathatobba-es-mindenki-szamara-konnyebben-hozzaferhetove-valnak-a-bethlen-gabor-alapkezelo-tamogatasai | VERIFIED (public article dated 2026-10-20) |
| BGA corporate site | https://bgazrt.hu/ | PARTIAL — programme pages; no documented open bulk API found in this audit |
| robots.txt | https://adattar.bgazrt.hu/robots.txt | VERIFIED — `User-agent: *` / `Disallow: /` |

## What the public article states

- Last five years of support data become searchable.
- Successful and unsuccessful applications are both represented at a basic level.
- Applicant tax identifiers are displayed as part of organizational disambiguation.
- Continuous upload/refresh; NIR-managed decisions update automatically; older paper-based individual requests upload monthly.
- Purpose: public transparency of public-fund decisions — **not** a complete diaspora organization directory.

## Technical access model observed

- UI stack: Jakarta Faces + PrimeFaces 15 map/report surface.
- Forms post back to `/adattar/riport/terkep.xhtml` (session-bound).
- No documented public REST/GraphQL/OpenAPI bulk export discovered during this audit.
- `robots.txt` disallows all agents.
- Internal JSF/AJAX endpoints are **not** an authorized bulk API.

## Licensing / reuse posture

| Question | Finding |
| --- | --- |
| Is the UI publicly viewable? | Yes, for interactive human search (subject to server controls). |
| Is unlimited automated copying authorized? | **Not evidenced.** robots disallow + no reuse license/export terms located. |
| Are tax IDs and applicant fields privacy-sensitive? | Yes — tax numbers and possible personal applicants require GDPR minimization; do not auto-publish into DORAPP profiles. |
| Lawful automation path today | Official documented API/export **or** steward-approved file drop. Otherwise remain blocked. |

## Adapter decision

Implement `scripts/bga_source_adapter.py` with three modes:

1. `official_api` — consumes a future documented API/export (not available now).
2. `approved_file_import` — imports steward-supplied normalized JSON/CSV snapshots with checksum + provenance.
3. `BLOCKED_LICENSE_OR_EXPORT` — default runtime mode: no live bulk fetch; writes blocker report and accepts fixtures only.

## Concept separation (mandatory)

Keep these as distinct record types:

- `BgaApplicant`
- `GrantApplication`
- `GrantDecision`
- `GrantAward`
- `UnsuccessfulApplication`
- `OrganizationCandidate` (DORAPP staging only)

Never equate:

- grant receipt ≠ NYEOMSZSZ membership
- grant receipt ≠ ongoing activity
- name match ≠ legal identity
- unsuccessful application ≠ absence of organization

## Access request template

Request from BGA / supervising ministry:

1. Machine-readable bulk export or API covering the full authorized five-year corpus.
2. Field dictionary and update cadence.
3. Explicit reuse terms for non-commercial public-interest directory linking.
4. Guidance on publishing tax IDs / personal applicants (expected answer: do not republish).

Until granted, DORAPP must not scrape the JSF map or circumvent session/CAPTCHA/bot controls.

## Blocker ID

`BLOCKED_LICENSE_OR_EXPORT` — no authorized bulk channel evidenced as of 2026-11-03.
