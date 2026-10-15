# DORAPP global entity, map, news and event contract (2026-10-15)

## Non-negotiable states
Every ISO territory has an explicit research status: UNRESEARCHED, IN_PROGRESS, VERIFIED_PRESENT, VERIFIED_NO_EVIDENCE, or NEEDS_REVIEW. The map renders VERIFIED_PRESENT green, VERIFIED_NO_EVIDENCE red, and all other states neutral. Never infer red from zero records. Store checkedAt, source URLs, query scope, reviewer/method and nextReviewAt for negative findings. Newly discovered evidence reopens a red territory. A territory is green only after documented country-level review, not after one candidate import.

## Organization identity and publication
Each verified organization has a stable ID, canonical public profile URL, country and location, type, localized name and introduction, official website, verified social profiles, public institutional contact details, history with dated sources, provenance, lastVerifiedAt, and current operational status. Maintain one entity across translations and sources; deduplicate aliases and previous names. Candidate-only records must not become indexable organization profiles. Protect personal information: publish individual profiles/contact data only with documented lawful basis and proportionate public-interest rationale; no private emails, home addresses or scraped private social data.

## Independent entity SEO/GEO/Schema/LLM
Each published organization profile has a server-rendered, crawlable canonical URL, distinct title/description/H1, contextual internal links, inclusion in sitemap, correct language and hreflang, and a stable JSON-LD @id. Use Organization and supported subtype, ProfilePage, BreadcrumbList and referenced WebSite/WebPage as appropriate. sameAs only for proven identity matches. Include verified founding date, area served, official contact and source links only when evidence exists. Ensure visible facts and JSON-LD agree. Do not promise Google indexing or rankings. Structured AI-readable exports may reuse canonical evidence; do not create contradictory shadow content.

## Press mentions (daily)
Maintain per-entity pressMention records: source URL, publication, headline, publication date, discoveredAt, checkedAt, language, matched entity ID, match evidence, relationship class (mention/interview/feature/official statement/other), and confidence/status. Search daily for new public references and recheck changed/removed links. Exclude same-name false positives, syndicated duplicates and unsupported affiliations. Display verified press items chronologically on the organization's own profile with outbound attribution. Human review or deterministic high-confidence source validation before publication; queue ambiguous hits.

## Events (daily)
Track official event feed URLs, ICS/RSS/structured events and approved public calendars by organization. Daily fetch with conditional requests, rate limits, retry/backoff and source provenance; normalize time zones, recurrence, cancellations, modifications and event identity. Upsert idempotently and preserve history; do not silently delete past events. Never treat third-party unverified listings as official. Expose valid Event JSON-LD on actual event detail pages only, with source and updatedAt.

## Automation and observability
Use existing repository generator and workflow architecture rather than duplicate jobs. Daily scheduled GitHub Actions: discover/update sources; validate; dedupe; stage uncertain changes; publish safe verified updates via reviewed PR or documented guarded auto-merge; rebuild pages/sitemaps/entity graphs; log metrics and failures. A failed fetch must not overwrite good data or mark an entity defunct. Record per-country last scan, coverage and source health. Monitor broken links and stale profiles. Do not assert the schedule is running until Actions execution is verified.

## GDPR, E-E-A-T and AI Trust
Document operator, editorial responsibility, lawful basis, retention, correction/removal mechanism, automated discovery/AI assistance and human verification boundaries in a transparent Trust Center. Consent-gate nonessential trackers and avoid scraping contrary to applicable rules. Distinguish media mention from endorsement, membership, partnership and employment. Verify schema syntax and semantics, indexing, WCAG accessibility, mobile map contrast, performance and exact live deployment. Never claim legal certification without legal review.

## Release gates
Implement incrementally in feature branches, run local/CI tests, open PRs, review country map status and entity page snapshots, then merge and verify production. Test red/green/neutral map semantics, press and event refresh, duplicate resistance, deleted/changed source handling, schema @id uniqueness, canonical/hreflang/sitemap and privacy controls. Existing country data and live design must not regress.
