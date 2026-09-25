# DORAPP Reference Architecture — Search / GEO / Schema / LLM / E‑E‑A‑T / AI Trust

Canonical production: https://diaszpora.kozpontiszovetseg.at/

## Authority model

DORAPP is designed as a source-backed national reference layer for Hungarian community life in Austria.

Primary authority chain:

1. canonical entity/profile page on DORAPP
2. canonical structured JSON record
3. explicit official or institutional evidence source attached to that record
4. public methodology and data-quality evidence
5. machine-readable entity and AI entry points

The system must never create authority by repetition. Unsupported facts remain absent.

## Search architecture

Indexable surfaces:

- / — national collection
- /szervezetek/{id}.html — canonical organization/entity profiles
- /oktatas/{id}.html — canonical education profiles
- /esemenyek/{id}.html — canonical Event leaf pages
- /tartomanyok/{state}.html — geographic collection pages
- /kategoriak/{category}.html — semantic collection pages
- /forrasok.html — methodology/AboutPage
- /adatminoseg.html — live transparency/data-quality page

Discovery:

- robots.txt
- sitemap.xml with evidence-derived lastmod values
- internal links from homepage, profile pages and event cards
- IndexNow notification after successful deployment

## Schema graph

Homepage: Organization publisher, WebSite, CollectionPage, Dataset.
Organization profiles: ProfilePage, Organization, BreadcrumbList, publisher relationship, source-backed parentOrganization/memberOf, optional verified founding/contact data.
Education profiles: ProfilePage, EducationalOrganization, BreadcrumbList, publisher relationship.
Event profiles: WebPage, Event, organizer Organization, Place/PostalAddress, Offer when available, performers when available, BreadcrumbList.
Geographic/category landing pages: CollectionPage, ItemList, BreadcrumbList.
Methodology/transparency: AboutPage, DataCatalog, publisher Organization.
Machine entity graph: /entity.jsonld.

## GEO / LLM reference layer

Machine entry points:
- /llms.txt
- /ai.txt
- /ai-entry.json
- /entity.jsonld
- /data/organizations.json
- /data/education.json
- /data/events.json
- /data/articles.json
- /forrasok.html
- /adatminoseg.html

Rules for AI citation:

- prefer canonical entity/event/education leaf URL for a specific claim
- use collection pages for navigation, not for facts absent from canonical records
- missing facts must not be inferred
- sourceUrl/evidenceSources remain the underlying evidence trail
- current event facts remain subordinate to the organizer's latest official source

## E‑E‑A‑T

Evidence of experience/expertise/trust is structural rather than promotional:

- identified publisher with ZVR 079797621
- operator/imprint link
- GDPR & AI Trust link
- public editorial methodology
- public data-quality status
- correction channel
- source-backed history fields
- machine-visible verification timestamps
- separation of automatic discovery from steward-maintained facts
- no analytics/tracking dependency for directory use

## Footer credit

Fejlesztette a Be Smart Kids Club csapata

with references to the Rólunk.at background article and business.vipach.at.

## Editorial rule

Do not optimize by keyword stuffing, doorway pages, invented local pages or unsupported schema.

Search visibility must derive from useful unique pages, entity clarity, complete source attribution, geographic and semantic internal linking, freshness, public correction policy, and structured data that matches visible content.
