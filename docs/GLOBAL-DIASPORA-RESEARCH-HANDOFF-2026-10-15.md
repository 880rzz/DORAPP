# Global Hungarian diaspora research handoff — 2026-10-15

## Scope and artifact
Seed: `data/global-diaspora-research-seed-2026-10-15.json`. This is **not** a publication-ready database. Every seed row is a named lead traced to an explicit directory source. Austria, Belgium, Canada and the United States already have canonical coverage; compare IDs before changes. The goal is comprehensive evidence-driven worldwide research across 249 ISO locations, without treating unresearched territories as empty or candidate names as confirmed organizations.

## Authority and architecture
Read `README.md`, `docs/REFERENCE_ARCHITECTURE.md`, `docs/PROFILE_STEWARD.md`, `docs/AUDIT-2026-10-15-MUSK-LENS.md` and active generators/validators first. Canonical country data: `data/countries/<iso2>/organizations.json`, `education.json`, `events.json`, `research-completion.json`; Austrian `data/organizations.json` etc. remain compatibility authority. Generated HTML is not a primary input. Do not modify `main` without validations. Use feature branches and PRs for staged research batches.

## Research inclusion
Include nonprofits, community groups, informal but publicly documented durable communities, churches, schools, youth and scout groups, folk dance/music, magazines/newspapers/radio/TV, independent professional event organizers and culturally relevant businesses, as separate entity classes with evidence. Persons only as publicly verifiable professional representatives of organizations/events, not as a broad personal registry, and only published professional contact channels.

Distinguish:
- actual registered legal organization vs informal community vs owned institution vs standalone class/event vs media publisher vs individual;
- formal membership, operational affiliation, collaboration, event organizer, host venue, person professional role;
- active, historical, unknown, closed with an explicit cessation source;
- missing channel vs unavailable site vs proof of cessation.

## Per-record mandatory research fields
ID stable within country; legal/official name, aliases, iso2, city/region when proven, entityClass/type/categories; factual 2-4 sentence intro; official website, Facebook, Instagram, other public social channels (nullable); public email/phone/contact page (nullable); `evidenceSources[]` with claim-specific institutional, registry and third-party links; `calendarSources[]` with URL, kind, scope and ingestEvents; `eventSources[]` where the validator supports; history/founded/milestones only with historical evidence; separately indexed press coverage. Store `profileVerifiedAt` only after first-party verification. Use `null` or omit for unverified fields. Never fabricate a link, affiliation, press appearance, founding date, event or address.

## Priority and country research
P0 national umbrella registers, diaspora project networks, diplomatic mission lists, national scout networks, minority/cultural organizations and credible specialist directories.
P1 focus: DE, GB, AU, NZ, AR, BR, UY, PY, ZA, NL, CH, SE, FR, IE, RO, SK, RS, UA, HR, SI, CZ, US, CA. Austria and Belgium: deduplicate and enrich, not restart.
P2 any other country with confirmed Hungarian community sources. A country can be truly verified-zero only after independent broad source review. Don't mark every ISO location as complete.

Run native-language combinations (Hungarian + local language + English) and category queries (magyar iskola, egyesület, Hungarian cultural association, Hungarian scout, magazine, club, events, local language equivalents), with city and region variants. Crawl umbrella membership pages as leads, resolve to first-party sites, validate current operations and source calendar links. Use external directories for leads, not as proof of every detailed field.

## Research execution
1. Parse seed and normalize Unicode aliases; deduplicate against existing global/Austrian canonical organization IDs, official domains and legal names.
2. Research P1 country batches in manageable PRs. Present an evidence table; separate publication-ready records from unresolved candidate names.
3. For each entity find own official website and official social channels, formal legal/contact data, founded/history, role-specific publicly named people, events feed, independently attributable reliable press links.
4. Write canonical JSON only with verified fields, keep missing data empty, update relevant articles index without inventing coverage.
5. Validate JSON, taxonomy, referential integrity, source URLs, duplicate entities, generated pages, JSON-LD, sitemap, canonical and language output, no GDPR regressions.
6. Open PR with files changed, numbers of verified/imported/duplicate/rejected/candidate items and CI state. Merge only when checks pass and report precise statuses.
7. Update country research status with an honest coverage statement. Do not claim global completion.

## Discovery audit finding
The existing discovery-sources for some countries contain plainly unrelated Wikipedia search hits (e.g. Germany/Australia/Argentina). Those are not organization records; a generic match to a country ISO code or Hungarian keyword is not enough. Require strong country + entity + active identity signals before any profile creation.

## Editorial and legal protection
Do not scrape private Facebook groups, member lists, private telephone numbers, residential addresses, children's information or non-consensual personal data. Record only official public business/institutional contacts. Distinguish public figures' officially published roles from personal biography. Cite source and access date; preserve corrections and exclusion rationale.

## Release
Generated public routes must be derived deterministically. CI and GitHub Pages must pass, representative live profiles checked before claiming production. The source seed should remain non-public-facing research input, not indexed as verified entity results.
