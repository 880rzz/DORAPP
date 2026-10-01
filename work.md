# DORAPP Global Hungarian Diaspora Platform — Build Specification

## Mission
Transform the current DORAPP repository into one global, source-backed directory and event platform for Hungarian diaspora communities in every country. Austria is the existing production reference and MUST be preserved while the architecture is generalized. BUILD the system; do not stop at an audit or proposal.

## Required end state
- Global homepage beginning with a single prominent autocomplete search above an accessible interactive world map.
- Every country represented; verified records produce derived organization counts on the map.
- World -> country -> first-level region -> city -> organization/program/event navigation.
- Worldwide autocomplete search across country, city, organization, activity and current/future program; full directory filtering may remain available inside country pages.
- Separate country subtree and canonical country dataset for every country.
- Verified profiles, education, event calendars and source health.
- One global current/future program calendar plus a country-filtered calendar on every completed country page.
- Global SEO/GEO/Schema/LLM/AI-trust structure.
- Automated validation, deployment and daily stewardship.

## Canonical architecture
Use one repository and main authority branch.
- `index.html`: global world-map homepage
- `countries/<iso2>/index.html`
- `countries/<iso2>/organizations/<id>.html`
- `countries/<iso2>/events/<id>.html`
- `countries/<iso2>/education/<id>.html`
- `data/global.json`: country registry, locales, research status and derived counts
- `data/countries/<iso2>/{organizations,events,education,source-health,articles,discovery-sources}.json`
- `skills/dorapp-global-steward/SKILL.md`
- `work.md`, `dailywork.md`

Use lowercase ISO 3166-1 alpha-2 country IDs. Derived counts MUST NOT be hand-maintained.

## Austria migration protection
Austria is live production data, not a prototype. Inventory current routes/data/workflows first. Add compatibility before moving files. Preserve existing Austrian public URLs through redirects or generated compatibility pages. Never lose organization/event/source history. Generalize mechanisms rather than exporting Austrian hard-coded exceptions. Deploy in reversible atomic stages.

## World map
The homepage MUST start with a responsive world map backed by maintained or repository-owned geographic data with ISO country IDs. Core navigation requires no map API key. Every country displays its current build-derived organization count on the map, counting civil/community and official/institutional organization records together while excluding child activities. Unfinished countries remain grey even when they already have verified records. Completed countries use the active map colour and are selectable. Distinguish unresearched, researching, partial, reviewed and verified-zero. Hover/focus/tap exposes country, count and status. Provide keyboard-accessible equivalent country list. Selecting a completed country opens `countries/<iso2>/`; unfinished countries are not presented as completed destinations.

## Global search
One reusable engine serves global and country pages. The global homepage autocomplete must suggest country, city, organization, activity and program as the user types. Country pages may additionally expose filters for first-level division, contact name/email/phone, address/venue and free text. Choices derive from current data, are locale-aware ABC sorted and narrow dependently. Filters use AND semantics. Results show live count, country and entity type. Organization selection includes child activities and owned events. Search aliases/diacritics without changing canonical spelling. Country pages preselect country. No third-party search dependency for the core directory.

## Country registry
Each country stores ISO2/ISO3, useful local/Hungarian/English names, locale(s), canonical first-level divisions, research status, last broad verification date and build-derived counts. “No records found yet” is never equivalent to “no Hungarian community exists”.

## Discovery scope
Research the full territory of every country using Hungarian, English and local-language queries. Include associations, umbrellas, informal communities, nurseries, schools/weekend schools, universities/student groups, folk dance/music, bands/choirs, theatre, scouts, libraries/book clubs, churches, family/youth/senior groups, private organizers, recurring initiatives, media and host institutions providing Hungarian services.

## Entity model
Base classes: organization, umbrella, group, project, activity, media, institution, host-institution. Model parentage, memberships, affiliations, operator/project/publisher/support/partner/host/regional-network relationships only from evidence. Shared domain/contact/address/social is not proof of identity or parentage. Do not inflate counts with events/classes/age groups.

## Evidence and social
Priority: official website -> first-party-linked official social -> official umbrella/member directory -> government/institution -> public-service media -> established diaspora/community media -> reliable secondary. Unknown facts remain empty. Never invent social vanity URLs, founders, dates, legal status or relationships.
Inspect website -> linked social -> Facebook/Events -> Instagram -> YouTube -> LinkedIn -> TikTok -> ticket platforms. Profiles, Events surfaces and individual events are distinct sources.

## Event authority
`calendarSources[].ingestEvents` is the sole ingestion authority; `eventSources` is compatibility metadata. Enable only stable, entity-scoped, processable calendars/lists/ICS/Event JSON-LD/feeds. Homepages, archives, shops, Linktrees, single tickets, generic host calendars and unparseable social profiles stay discovery-only. Mixed calendars require data-driven inclusion rules. Never attribute member events from umbrella aggregate calendars to the umbrella.

## Source health
Differentiate content-invalid, blocked, rate-limited, parser-gap, TLS/network and transient failures. 403/429/timeout alone is not evidence for removal. Retired sources must not remain active failures.

## Daily freshness
Implement `dailywork.md` as resumable country batches with bounded concurrency. A country failure must not block other countries. Event freshness runs globally; broad discovery rotates by research status and age.

## SEO, GEO, Schema and AI
Generate canonical URLs, hreflang where appropriate, global/country/profile/event sitemaps plus sitemap index, robots, appropriate WebSite/Organization/CollectionPage/Dataset/Event/BreadcrumbList JSON-LD, entity graph, llms.txt, ai.txt, source/correction policy and crawlable world -> country -> region -> entity links. Structured data mirrors visible verified facts.

## Validation gates
Block release on invalid JSON; duplicate/conflicting IDs; invalid ISO/country or relationship IDs; taxonomy/evidence errors; duplicate canonical socials requiring review; legacy-only event sources; event authority conflicts; semantic duplicate/orphan events; invalid routes; stale derived counts; broken map links; invalid global search index; JS/static/sitemap/schema failures.
Required invariants: legacy-only event sources = 0; authority conflicts = 0; orphan events = 0; broken country IDs = 0; hand-entered derived counts = 0.

## Race protection
Before every write read current main HEAD and target blob SHA; immediately before writing read them again. If changed, rebase intended work onto latest state. Never restore an old snapshot or overwrite newer human/workflow/agent work.

## Autonomous loop
inspect -> verify -> implement -> validate -> commit -> workflows -> deploy -> live verify -> continue. Autonomously perform evidence-backed fixes, architecture required here, validators, generators, migrations, tests and deployment repairs. Stop only for unresolved evidence/ownership/legal/taxonomic conflicts or destructive decisions not specified here.

## Build order
1. Protect and validate Austria.
2. Add global country registry and country-scoped data abstraction.
3. Add Austrian compatibility/migration.
4. Generalize worldwide search.
5. Build accessible world map and derived counts.
6. Generate country subdirectories/static routes.
7. Generalize profile/event/education generators.
8. Generalize curator/source-health/taxonomy workflows per country.
9. Add global sitemap/schema/AI discovery.
10. Run regression tests.
11. Deploy and verify global homepage and Austria.
12. Complete the Netherlands as the next full country build.
13. After the Netherlands reaches all quality gates, build the United States as the next full country.
14. Expand remaining countries in deterministic evidence-backed batches.
15. Continue until every country is explicitly tracked with research status; never fabricate content to simulate coverage.

## Definition of done
Documentation alone is not completion. World map, global search, country routing, Austria compatibility, validators, daily workflows, structured metadata and production deployment must operate together.
