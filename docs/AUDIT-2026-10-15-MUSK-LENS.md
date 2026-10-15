# DORAPP first-principles audit — 2026-10-15

## Executive verdict

The system is unusually strong for a static community directory: evidence is canonical, publication is deterministic, trust artifacts are public, and deployment is automated. It is not yet operationally simple. The largest risk is not missing features; it is duplicated authority across Austrian compatibility data, global country data, multiple generators and several workflows that can all write generated output to `main`.

“Is it well documented?” Partly. The source/evidence rules are strong, but the architecture documents had drifted to the retired domain and Austria-only model. This audit updates those documents and makes the current global authority chain explicit.

Scores are directional engineering judgments, not legal or certification results:

| Area | Before | After this change | Main remaining constraint |
| --- | ---: | ---: | --- |
| Documentation | 6/10 | 8/10 | rules remain split across several files |
| Frontend | 7/10 | 8/10 | no automated browser/visual regression suite |
| Backend/data pipeline | 7/10 | 7/10 | multiple main-writing workflows and rebuild churn |
| SEO | 8/10 | 8/10 | shared OG media and legacy compatibility surface |
| GEO | 8/10 | 8/10 | address normalization is still partly free-form |
| Schema | 7/10 | 8/10 | publisher IDs/types still differ across generators |
| GDPR | 8/10 | 9/10 | external-provider disclosure must stay current |
| E-E-A-T | 8/10 | 8/10 | record-level reviewer/editor identity is limited |
| LLM readiness | 8/10 | 8/10 | duplicated machine surfaces need drift checks |
| AI Trust | 8/10 | 8/10 | relationship semantics need continued enforcement |

## First-principles lens

### 1. Make the requirement less wrong

The product is not “a website with a map.” It is a verifiable entity graph with human navigation. The non-negotiables are evidence, currentness, relationship semantics, explicit research status, accessible discovery and deterministic publication.

A “complete country” is a research state, not a color or a nonzero count. A contact channel is an intentional user action, not a tracking dependency.

### 2. Delete

High-value deletion targets:

- remove retired-domain language and Austria-only assumptions from active architecture docs;
- eliminate per-generator footer wording differences through one shared invariant;
- stop treating generated-output commits as meaningful content changes in human review;
- eventually remove the Austrian compatibility mirror once redirects, canonical routes and downstream consumers no longer require it.

Do not delete evidence history, compatibility URLs or records merely to reduce file count.

### 3. Simplify

P1: define one reusable footer/publisher/contact component at generation time. The shared `ui.js` fallback now guarantees attribution and WhatsApp access, but server-visible markup should continue for SEO and non-JavaScript use.

P1: converge publisher `@id` values (`#publisher` vs `#organization`) and schema construction through one helper module.

P1: centralize the ready-country predicate and public research-state labels so map, search, sitemap, country pages and calendars cannot diverge.

### 4. Accelerate

Run fast deterministic validators on every push; keep external source crawling scheduled or manually triggered. Cache source checks by normalized URL and freshness window. Separate content commits from generated-output commits in reporting.

### 5. Automate

Add browser tests at desktop and mobile widths for:

- world map render and completed-country coloring;
- navigation, focus order and zoom controls;
- consent accept/reject/reopen;
- WhatsApp target, accessible name and no pre-click network request;
- footer attribution;
- long names, e-mail addresses and translated country labels;
- JSON-LD extraction from representative global and Austrian routes.

Add a machine-readable release manifest containing source commit, generated commit, validation timestamp and deployed production URL.

## Frontend

Strengths: the homepage is the actual directory, the map has an accessible list equivalent, filters are task-oriented, shared mobile navigation exists, and analytics is not required for core use.

Resolved now:

- consistent BMI/Be Smart Kids Club authorship;
- floating, keyboard-accessible WhatsApp action;
- no WhatsApp SDK or pre-click transfer;
- consent banner suppresses the floating control to prevent overlap;
- global event profiles now receive a footer;
- shared-controller cache version is bumped.

Remaining: no browser/visual regression evidence; `styles.css` is a growing monolith; footer markup is repeated even though runtime fallback is shared.

## Backend and data flow

Strengths: canonical JSON, deterministic generators, validators, source-health separation, semantic event deduplication and research-completion artifacts.

Highest risk: several workflows can generate, commit and push overlapping artifacts. Rebase/rebuild loops reduce corruption risk but produce churn, cancelled deploys and harder incident reasoning.

Recommended target: one source-change lane and one build/deploy lane. Scheduled researchers should commit canonical/audit data; a single build workflow should generate and deploy artifacts from an immutable source SHA.

## SEO and GEO

Strengths: canonical URLs, sitemap, robots, country/region/category/entity routes, ISO country registry, area coverage and repository-owned maps.

Remaining: enforce one publisher/entity graph; normalize address components; treat unfinished country routes consistently; ensure compatibility routes do not compete with canonical global routes.

## Schema

Strengths: ProfilePage, Organization/EducationalOrganization/Event, Dataset/CollectionPage and BreadcrumbList coverage.

Resolved now: BMI address is exposed to legacy profile schema, public contact becomes a ContactPoint, and public leadership is rendered from canonical `people[]`.

Remaining: define role semantics before mapping every public person to `employee`, `member` or `founder`. Do not overclaim schema relationships.

## GDPR

The consent-first controller is sound in principle. This change aligns the measurement ID with policy: `G-1FC22JEX2F`.

WhatsApp is an external link only. No Meta/WhatsApp script, pixel, cookie or iframe loads on page view. The visitor leaves DORAPP only after activation.

Keep the linked privacy notice current about Google Analytics, WhatsApp and external map/navigation providers. This is engineering analysis, not legal advice.

## E-E-A-T, LLM and AI Trust

Strengths: named publisher with ZVR, evidence URLs, verification dates, correction channel, methodology, quality page, `llms.txt`, `ai.txt`, `ai-entry.json`, `entity.jsonld` and canonical data.

Resolved now: architecture documentation matches the global system; official BMI leadership/contact/parent facts are visible and sourced.

Remaining: add explicit editorial responsibility only where governance supports it; validate drift between visible claims, JSON-LD, canonical JSON and machine entry files; keep uncertainty and technical source failures explicit.

## Verified BMI facts

Sources checked 2026-10-15:

- [Bécsi Magyar Iskola official contact page](https://www.magyariskola.at/kapcsolat);
- [Központi Szövetség official site](https://www.kozpontiszovetseg.at/);
- [Be Smart Kids Club official BMI program page](https://www.magyariskola.at/event-details/besmartkidsclub);
- [Rólunk.at background article](https://rolunk.at/aktualis/a-fiataloknak-ma-mar-bizonyitek-kell-egy-becsi-kreativ-kozosseg-uj-generaciot-epit/).

Canonical changes: BMI becomes a child institution of `kozponti-szovetseg`; address, public leadership, `marketing@kozpontiszovetseg.at`, and `+43 677 616 555 92` are stored with official evidence.

## Decision backlog

1. P1: consolidate main-writing workflows and generated-output ownership.
2. P1: add browser/visual/accessibility regression tests.
3. P1: unify footer and publisher/schema helpers.
4. P2: normalize postal addresses into structured fields.
5. P2: add release manifest and production smoke test.
6. P2: validate machine-entry drift.
7. P3: split CSS and generator templates after shared invariants have tests.
