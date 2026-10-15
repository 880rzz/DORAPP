# DORAPP reference architecture — Search / GEO / Schema / LLM / E-E-A-T / AI Trust

Canonical production: https://www.diaszporaterkep.hu/

## Purpose and authority

DORAPP is a source-backed global directory and event calendar for Hungarian diaspora communities. Austria is the mature compatibility dataset; the global country model is authoritative for worldwide navigation.

Truth chain:

1. canonical country or Austrian compatibility data;
2. generator/shared component;
3. generated public output;
4. validator and automated audit;
5. GitHub Actions build;
6. GitHub Pages deployment and representative live verification.

Generated HTML is never edited as the primary fix when canonical data or a generator can resolve the issue once.

## Canonical surfaces

- `data/global.json`: ISO country registry, research status and derived counts;
- `data/countries/<iso2>/`: country organizations, education, events and research completion;
- `data/organizations.json`, `data/education.json`, `data/events.json`: Austrian canonical compatibility authority;
- `scripts/generate_*.py`: deterministic publication layer;
- `world.js`, `country.js`, `ui.js`, `styles.css`: shared interaction and presentation layer.

## Public routes

- `/`: world map, global search, reviewed organizations and programs;
- `/countries/<iso2>/`: country collection;
- `/countries/<iso2>/{organizations,education,events}/<id>.html`: global entity leaves;
- `/szervezetek/`, `/oktatas/`, `/esemenyek/`: Austrian compatibility leaves;
- `/tartomanyok/`, `/kategoriak/`: Austrian geographic and semantic collections;
- `/forrasok.html`, `/adatminoseg.html`: methodology and live transparency.

## Research states

`unresearched`, `researching`, `partial`, `reviewed`, and `verified-zero` are distinct. Only `reviewed` and `verified-zero` countries are presented as completed and included in ready-country search, calendar and sitemap surfaces. Counts are build-derived.

## Search, GEO and Schema

Canonical URLs use `https://www.diaszporaterkep.hu`. Sitemap, robots, internal links and country/entity routes must agree.

The schema graph uses WebSite, Organization publisher, Dataset/CollectionPage, ProfilePage, Organization/EducationalOrganization/Event, Place/PostalAddress and BreadcrumbList as appropriate. Structured data must mirror visible verified facts. Parent, membership and affiliation semantics are not interchangeable.

GEO identity is represented by ISO country, region/state, city, areaServed and address. The repository-owned world map has ISO identifiers and no map API dependency.

## GDPR and direct contact

Analytics uses GA4 `G-1FC22JEX2F` only after explicit consent through `ui.js`. Core directory functions do not depend on analytics. Consent can be accepted, rejected and reopened.

The WhatsApp control is an ordinary external link to `+43 677 616 555 92`. No WhatsApp resource, cookie or SDK loads before an intentional click. The external provider receives data only after the visitor activates the link.

## E-E-A-T and AI trust

Trust is structural:

- identified publisher and ZVR `079797621`;
- visible evidence sources and verification timestamps;
- public methodology, data-quality report and correction channel;
- protected steward fields and explicit relation types;
- separate technical source health from organizational status;
- no invented data or authority by repetition.

Machine entry points: `/llms.txt`, `/ai.txt`, `/ai-entry.json`, `/entity.jsonld`, canonical JSON and leaf pages. Specific claims should cite the canonical leaf and its evidence trail.

## Authorship and contact

The required footer attribution is: “A Bécsi Magyar Iskola – Be Smart Kids Club csapata hozta létre.”

Official project contact: `marketing@kozpontiszovetseg.at`.

The canonical Bécsi Magyar Iskola record is a child institution of `kozponti-szovetseg`, with public contact and leadership data supported by the official BMI contact page.

## Release gate

Required checks include JSON parse, Python compile, JavaScript syntax, directory/global/static validation, generators, semantic duplicates, sitemap/canonical agreement, JSON-LD parse, consent-first analytics, shared UI presence, link/human-language/ecosystem audits, Actions success, deployment and representative live checks.

See `docs/AUDIT-2026-10-15-MUSK-LENS.md` for the current first-principles audit and remaining priorities.
