# DORAPP research KPI definitions (2026-11-03)

These metrics are not interchangeable. A successful Actions run is not organization verification, country completion, or production publication.

| KPI | Meaning | Increments when | Does not mean |
| --- | --- | --- | --- |
| `country_attempted` | Research batch selected a country | Cursor advances / country listed in `countriesAttempted` | Sources worked or entities found |
| `sources_queried` | Discovery attempted against a configured source | HTTP/query started under policy | Useful result |
| `source_success` | Source returned usable, parseable evidence payload | Non-error payload meeting source contract | Candidate quality |
| `candidate_found` | Raw discovery hit entered staging/queue | New unresolved candidate record | Hungarian diaspora relevance |
| `candidate_qualified` | Candidate passed deterministic relevance gates | Language/location/org-class filters pass | First-party proof |
| `first_party_confirmed` | Official site/registry confirms identity and location | First-party check status is confirmed | Human publication approval |
| `review_approved` | Human steward approved evidence package | Explicit review decision recorded | Already live in production |
| `published` | Canonical public dataset + generated pages include the entity | Merge + deploy of approved record | Country coverage complete |
| `country_coverage_assessed` | Source checklist executed and gaps documented | Coverage assessment artifact written | Country complete |
| `country_complete` | Predeclared closure checklist fully evidenced | Every required source class assessed with documented outcome | One green research run |

## Supporting states

- `REJECTED`, `STALE`, `DISPUTED`, `NEEDS_REVIEW` are first-class and must remain countable.
- Historical membership and unsuccessful grants are retained as evidence classes, never counted as newly verified organizations.
- `promotion-ready.json` count is independent from `verification-queue.json` and from `research-state.cycleProgress`.

## Baseline snapshot (re-check before claiming improvement)

Observed at commit `e310cac87e0dbdf46e118f776f9c4c82aab60bc1` (2026-11-03):

- `data/global.json`: 249 countries; `researching=151`, `reviewed=5`, `unresearched=93`.
- `data/research-state.json`: `lastRunAt=2026-11-02T09:54:23+00:00`, `cycleProgress=28/249`, `countriesAttempted=["eh"]`.
- `data/verification-queue.json`: 38 items, all `no-strong-first-party-proof`.
- `data/promotion-ready.json`: 0 items.
