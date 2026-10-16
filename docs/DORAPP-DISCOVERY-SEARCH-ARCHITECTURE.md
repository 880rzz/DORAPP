# DORAPP — global discovery and search architecture

## Coverage
Include registered associations, informal Hungarian communities, umbrella organizations and their members, schools, churches, scouts, cultural and business networks, Hungarian-language or Hungarian-community media, event organizers, events, and attributable press mentions. Registration is not a prerequisite for inclusion.

## Discovery pipeline
1. Discover candidates using Hungarian, English and relevant local-language country/city searches; public federation member lists, official directories, organization links, publicly accessible community pages, event calendars, and press references.
2. Follow relationship edges (umbrella → member, organizer → event, media → mentioned entity, organization → partner), with bounded crawl depth and canonical URL deduplication.
3. Record source URL, observed date, locale, discovery method, entity type, and confidence separately. Do not interpret a missing result as proof that an entity does not exist.
4. Verify identity and locality against attributable first-party, institutional or independent evidence. A public Facebook page can substantiate an informal community; never bypass access restrictions or scrape private profiles.
5. Publish only verified entities; retain candidate and needs-review queues separately. Provide correction and takedown channels.
6. Refresh upcoming events and press references daily; recheck stable organization profiles by staleness and change signals. Remove expired events from upcoming listings without deleting provenance.

## Search UX acceptance criteria
- Autocomplete starts at first typed character, accent-insensitive and case-insensitive; query “At” should offer matching Atlanta entities if they exist in the verified index.
- Search country, city, organization, informal group, media, event and activity with explicit type and location labels.
- Rank exact/prefix matches before general substring and metadata matches; deduplicate and link to canonical detail pages.
- Keyboard ArrowUp/ArrowDown/Enter/Escape, screen-reader combobox/listbox semantics, focus recovery and mobile touch must work.
- Distinguish no verified match from index unavailable; no fake suggestions.
- Keep verified results searchable even when country-level research is incomplete.
- Add automated tests for prefixes, diacritics, ranking, invalid links, freshness and accessibility.

## Release gates
Measure discovery throughput and failure rates; use bounded batch sizes, retries and rate limiting. Run existing validators and smoke tests before merge. Publish only after CI passes and staging/mobile QA is documented. GitHub scheduled tasks are orchestration, not an unrestricted internet crawler.
