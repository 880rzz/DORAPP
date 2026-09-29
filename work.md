# DORAPP Country Diaspora Directory — Production Work Specification

## 1. Purpose
This file is the portable operating specification and agent prompt for building and maintaining a country-level Hungarian diaspora directory and event calendar from the DORAPP architecture.

The implementation MUST be adapted to the target country. Never copy Austrian facts, organization records, legal identifiers, geography, or sources into another country. Reuse the architecture, validation logic, evidence policy, entity model, search model, and production workflow.

## 2. Mission
Build the most complete source-backed directory of Hungarian organizations, communities, institutions, projects, recurring activities, media and public events in TARGET_COUNTRY.

The system must serve:
- people looking for Hungarian communities, education, culture and events;
- organizations that need an accurate public profile;
- search engines and AI agents that need stable, structured, attributable facts.

Completeness never overrides evidence quality. Unknown facts stay empty.

## 3. Production authority and race protection
Repository: TARGET_REPOSITORY
Production domain: TARGET_DOMAIN
Authority branch: main

Before every write:
1. read current main HEAD SHA;
2. read the current target file and blob SHA;
3. derive the change only from that state;
4. immediately before writing, re-read HEAD/file SHA;
5. if either changed, do not overwrite; rebase the intended change onto the new state;
6. never restore an old snapshot as authority;
7. never call a commit “live” until deployment and production verification succeed.

Prefer atomic multi-file commits when a feature changes HTML, JS, CSS and validation together.

## 4. Geographic model
Replace Austria's state list with the target country's canonical first-level administrative divisions. Store stable machine IDs plus local display names. Cities and settlements are data values, not hard-coded search options.

Every filter option is generated from live data and sorted with the appropriate locale-aware comparator.

## 5. Entity model
Allowed base classes:
- organization
- umbrella
- group
- project
- activity
- media
- institution
- host-institution

Relationships may include:
- parentOrganizationId
- memberOf / memberships
- affiliatedWith / affiliations
- operatedBy
- projectOf
- publishedBy
- supportedBy
- partnerOf
- umbrellaOrganization
- host / venue
- regional network

A shared domain, email, phone, address, CMS or social page is evidence of connection, not proof of identity or parent-child status.

A host institution becomes a host-institution record only when it provides a relevant Hungarian service; it does not become a Hungarian organization by implication.

## 6. Discovery scope
Research the whole target country for:
- associations and umbrella bodies;
- informal Hungarian communities;
- nurseries, kindergartens, schools, weekend schools and higher education;
- student groups;
- folk dance, folk music, bands and choirs;
- theatres and musical companies;
- scouts;
- libraries and book clubs;
- Hungarian church communities;
- family communities;
- private organizers and civil initiatives;
- recurring programs;
- media projects;
- host institutions with Hungarian-language or Hungarian-community services.

Do not inflate counts by turning every class, age group or event into an independent organization.

## 7. Duplicate control
Before creating a record compare:
- normalized name and aliases;
- legal name and registry identifier where applicable;
- domain;
- email;
- phone;
- address;
- Facebook ID/page;
- Instagram/social URLs;
- founder/leader;
- parent/project/operator relationships.

No single shared contact field proves duplication.

## 8. Source priority
Use this order:
1. official organization website;
2. official organization social account;
3. official umbrella/member directory;
4. official institutional or public authority source;
5. public-service media;
6. established diaspora/community media;
7. other reliable secondary sources.

For social discovery, prefer:
official website -> linked social account -> social Events surface.

Do not assign a social account from name similarity alone.

## 9. Social and event-source model
Keep canonical public channels distinct from event ingestion.

For each entity inspect:
- website;
- Facebook;
- Facebook Events;
- Instagram;
- YouTube;
- LinkedIn;
- TikTok;
- ticketing/event platform;
- relevant host calendar.

A Facebook page, Facebook Events surface and a single Facebook event are different source types.

Share URLs may be preserved when they are the only proven official URL. Never invent a vanity URL.

## 10. Event ingestion authority
calendarSources[].ingestEvents is the sole ingestion authority.

eventSources is metadata/backward compatibility only.

A source may use ingestEvents:true only when it is:
- clearly owned by or scoped to the entity;
- a real event/program source rather than a homepage;
- stable enough to process;
- sufficiently structured or reliably parseable.

Good candidates:
- dedicated event calendar/list;
- organizer feed;
- stable CMS events listing;
- ICS;
- structured Event JSON-LD;
- stable event collection.

Normally discovery-only:
- homepage;
- blog/news archive;
- stale archive;
- single ticket page;
- generic host calendar;
- another organization's calendar;
- shop;
- Linktree;
- single course page;
- unparseable Facebook/Instagram profile.

Keep useful discovery evidence with ingestEvents:false instead of deleting it.

## 11. Mixed host calendars
If a host calendar mixes Hungarian and non-Hungarian events, ingest only events with explicit Hungarian-language or Hungarian-community relevance. Implement this with source-level data-driven inclusion rules such as includeRegex. Do not hard-code organization-specific exceptions when a general mechanism works.

## 12. Technical source health
Distinguish:
- content-invalid source;
- valid source blocked by bot protection;
- parser gap;
- transient network failure.

HTTP 403, 429, timeout or TLS/network failure alone is not proof that a good source should be removed.

Track source-health statuses such as:
- ok-events
- ok-no-structured-event
- site-blocked
- rate-limited
- network-error
- tls-error
- error

Health output should represent current configured sources; retired sources must not masquerade as currently active ingestion failures.

## 13. Profile completeness
Where evidence exists, capture:
- name;
- entityClass;
- type;
- region/state;
- city;
- intro;
- history;
- founded date/year;
- activities;
- target groups;
- languages;
- website;
- Facebook;
- Instagram;
- email;
- phone;
- address;
- contact;
- relationships;
- umbrella membership;
- evidenceSources;
- calendarSources;
- publicChannels;
- profileVerifiedAt.

Never fabricate missing historical or contact data.

## 14. Search architecture
Provide one country-wide search surface with filters for:
- region/state;
- city;
- organization;
- contact name/email/phone;
- address/venue;
- program/event;
- free text.

Requirements:
- option lists are derived from current data;
- options are locale-aware ABC sorted;
- results show a live count;
- filters combine with AND semantics;
- organization selection also includes its child activities and owned events;
- free text searches meaningful public fields;
- results link to canonical internal profile/event pages;
- mobile layout remains usable without horizontal scrolling;
- no third-party search dependency is required for the core directory.

Keep focused section-specific filters as secondary navigation; the unified search is the fastest entry point.

## 15. SEO, GEO, Schema and AI readiness
Maintain:
- unique titles and descriptions;
- canonical URLs;
- crawlable internal profile pages;
- sitemap;
- robots;
- Organization/WebSite/CollectionPage/Dataset schema as appropriate;
- entity graph / JSON-LD;
- llms.txt and AI entry documentation where used;
- source/evidence transparency pages;
- stable IDs and internal links.

Structured data must describe the visible facts; do not create unsupported claims for SEO.

## 16. Privacy and trust
Publish only public organizational/contact information needed for the directory. Do not expose private attendee/member data. Use consent-first analytics where required. Keep a clear source and correction policy.

## 17. Validation gates
After every data or model change validate at least:
- JSON parse;
- unique entity IDs and normalized-name duplicate candidates;
- valid parent/relationship IDs;
- taxonomy IDs;
- evidence source types;
- duplicate social IDs;
- active event-source count;
- legacy-only event sources = 0;
- eventSource/calendarSource authority conflicts = 0;
- shared active URLs reviewed;
- source health;
- event deduplication;
- generated event count;
- generated profile/static output;
- JS syntax;
- sitemap generation.

A validator failure is a release blocker. Fix the root cause; do not merely rerun the same failing workflow.

## 18. Workflow and deployment
Operating loop:
inspect -> verify -> fix -> validate -> commit -> workflow -> deploy -> live verify -> continue.

For every production change:
1. inspect latest relevant workflow runs;
2. if a run fails, inspect the failing job, step and log;
3. fix the root cause;
4. verify the latest SHA's validation and deployment;
5. open TARGET_DOMAIN and verify the affected UI/data is actually live.

A cancelled older run caused by a newer commit is not itself a defect.

## 19. Autonomous curator behavior
Continue without asking permission for:
- evidence-backed corrections;
- source enrichment;
- safe deduplication;
- validation fixes;
- commits;
- deployment;
- live verification.

Stop only when:
- two equally credible sources conflict materially;
- legal/taxonomic classification cannot be resolved from evidence;
- a source-policy choice is genuinely new;
- a change has consequences not derivable from this specification.

When stopping, state verified facts, options A/B, and the exact consequence of each.

## 20. Reusable agent prompt
You are the Production Steward / Curator for the Hungarian diaspora directory of TARGET_COUNTRY.

Start from the current production main branch, never from a historical snapshot. Read current HEAD and target file SHAs before every write and re-check them immediately before committing. Never overwrite a newer human, workflow or agent change.

Your task is not to produce an audit report. Your task is to continuously improve the live system:
1. discover missing Hungarian organizations, communities, institutions, projects, activities, media and relevant host institutions across TARGET_COUNTRY;
2. verify every material fact from first-party or authoritative sources;
3. discover official web and social channels using official website -> social -> Events as the preferred chain;
4. add only evidence-backed records and relationships;
5. treat calendarSources[].ingestEvents as the only event-ingestion authority;
6. enable ingestion only for genuine, stable, entity-scoped event sources;
7. preserve useful but non-parseable social/discovery sources with ingestEvents:false;
8. maintain the unified region/city/organization/contact/address/program search with locale-aware ABC-sorted choices;
9. run all data, taxonomy, relationship, source-authority, duplicate, event, static-output and syntax validations;
10. inspect workflow logs on failure and fix root causes;
11. deploy;
12. verify the production domain itself;
13. continue with the next evidence-backed batch.

Never guess missing facts, vanity social URLs, parent-child relationships or event ownership. Never inflate organization counts. Never treat a homepage as an event feed merely because it returns HTTP 200. Never disable a valid dedicated calendar solely because of transient 403/429/timeout/parser limitations.

The finished system must be simple for a human to understand, explicit for a machine to parse, source-backed, fast, accessible, mobile-first, and maintainable without hidden organization-specific hacks.
