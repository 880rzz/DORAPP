# DORAPP NYEOMSZSZ baseline audit — 2026-11-03

**Contract:** [Issue #59](https://github.com/880rzz/DORAPP/issues/59)  
**Baseline SHA:** `e310cac87e0dbdf46e118f776f9c4c82aab60bc1`  
**Production:** https://www.diaszporaterkep.hu  
**Auditor:** Cursor cloud agent execution against live repo + public sources  
**as_of:** 2026-11-03T05:47:55Z (UTC) / 2026-11-03 06:47 Europe/Vienna

Status vocabulary for every claim below: `VERIFIED`, `PARTIAL`, `FAILED`, `NOT CHECKABLE`.

## 1. Source of truth and branch state

| Claim | Status | Evidence |
| --- | --- | --- |
| `main` is current working base and clean | VERIFIED | `git status` clean; `origin/main` at `e310cac8` |
| Issue #59 is open execution contract | VERIFIED | `gh issue view 59` state OPEN, created 2026-11-03T05:39:42Z |
| Global registry has 249 ISO countries | VERIFIED | `data/global.json` `countryUniverseSize=249`, `len(countries)=249` |
| Research statuses researching/reviewed/unresearched = 151/5/93 | VERIFIED | Counter over `researchStatus` |
| Research cursor at 28/249 after EH attempt | VERIFIED | `data/research-state.json` `lastRunAt=2026-11-02T09:54:23+00:00`, `countriesAttempted=["eh"]` |
| Verification queue is 38 non-promotable candidates | VERIFIED | all `firstPartyStatus=no-strong-first-party-proof`; includes false positives such as Wikipedia “Education in Bosnia and Herzegovina” |
| Promotion-ready queue empty | VERIFIED | `data/promotion-ready.json` `items=[]` |

## 2. Workflow / cron / CI / Pages

| Claim | Status | Evidence |
| --- | --- | --- |
| Live steward schedule is daily only (`37 2 * * *`) | VERIFIED | `.github/workflows/global-daily-steward.yml` on `main` |
| Hourly research from #37/#41 is not active on `main` | VERIFIED | #37 merge `5e47088…`, #41 merge `0b144fad…` restored hourly; later #48 commit message explicitly “run global research daily rather than hourly” removed `37 0-1,3-23 * * *` |
| Recent steward schedule runs are ~daily, not hourly | VERIFIED | `gh run list --workflow=global-daily-steward.yml` successes on 2026-11-02, 11-01, 10-31… (~24h spacing) |
| Steward still pushes directly to `main` | VERIFIED | workflow step `git push origin HEAD:main` |
| Static build workflow still pushes generated profiles to `main` | VERIFIED | `.github/workflows/deploy-pages.yml` persist step |
| PR #40 (PR-only publication gate) remains open / unmerged | VERIFIED | https://github.com/880rzz/DORAPP/pull/40 |
| PR #42 (search/map honesty) remains open | VERIFIED | https://github.com/880rzz/DORAPP/pull/42 |
| PR #46 (steward PR pipeline + `steward_schedule.py`) remains open | VERIFIED | https://github.com/880rzz/DORAPP/pull/46 |
| Latest production smoke failed on ES organizations JSON | VERIFIED (historical) | run [41452864144](https://github.com/880rzz/DORAPP/actions/runs/41452864144) `es: invalid JSON /data/countries/es/organizations.json` at 2026-11-02T13:27:33Z |
| Live ES organizations.json is valid JSON now | VERIFIED | HTTP 200, `application/json`, parses; size 37525; required key `organizations` present (checked 2026-11-03) |
| ES smoke root cause is durable syntax corruption in git | FAILED to confirm | Repo file parses; likely deploy/CDN race or transient non-JSON body during Pages propagation. Smoke should classify HTML/404/empty separately from `json.loads` failure. |
| Pages deploy around the smoke window succeeded | VERIFIED | Issue baseline cites run 41452848497; smoke still failed afterwards |

## 3. NYEOMSZSZ membership conflict

| Claim | Status | Evidence |
| --- | --- | --- |
| Homepage claims 17 member countries | VERIFIED | EN/DE/SV homepage prose |
| Directory lists 20 named organizations | VERIFIED | https://www.nyeomszsz.org/tagszervezeteink/ headings 1–20 |
| Directory-only vs homepage country list: BA, IE, MK | VERIFIED | see `data/nyeomszsz/membership-source-reconciliation.json` |
| England / Great Britain wording conflict | VERIFIED | Directory “Anglia”; homepage “Great Britain” |
| Island of Ireland must not auto-map NI/UK | VERIFIED | Directory label “Ír-sziget”; country page incomplete (“Készül”); no website observed |
| FEMAF country-page website target disputed | PARTIAL | FR country page links to `magyarutca.org` (FI association site) |

Artifact: `data/nyeomszsz/membership-source-reconciliation.json` + seeds in `data/nyeomszsz/discovery-seeds.json`.

## 4. NYEOMSZSZ target country data coverage (not completion)

Research scope ISO2: AT BA CH CZ DE EE ES FI FR GB IE IT LT LV MK NL NO PL PT SE.

| ISO | `researchStatus` | Canonical orgs file | Notes |
| --- | --- | --- | --- |
| AT | reviewed | yes (legacy mirror + country file) | Mature Austria corpus; not proof of NYEOMSZSZ network completeness |
| NL | reviewed | yes | Reviewed ≠ exhaustive |
| ES | unresearched in registry / partial in file | yes (12 orgs) | Registry status lags country file |
| DE GB SE | researching / mixed | sparse files | Not coverage-complete |
| BA CH CZ EE FI FR IE IT LT LV MK NO PL PT | mostly unresearched or researching | mostly missing `organizations.json` | No country may be marked complete |

Coverage assessment status: **PARTIAL** — inventory only; closure checklist not satisfied for any target country in this PR.

## 5. BGA feasibility

See `docs/audits/BGA-INTEGRATION-FEASIBILITY-2026-11-03.md`.

| Claim | Status |
| --- | --- |
| Official bulk API/export located | FAILED |
| robots.txt disallows all agents | VERIFIED |
| Public article describes 5-year successful+unsuccessful corpus with tax IDs | VERIFIED |
| Live scraping authorized | FAILED (not evidenced; blocked) |
| Adapter default mode | `BLOCKED_LICENSE_OR_EXPORT` |

## 6. UI / SEO / trust surfaces (spot checks)

| Claim | Status | Evidence |
| --- | --- | --- |
| Production homepage loads | VERIFIED | smoke + live fetch |
| Canonical / schema markers present on AT country page | VERIFIED | smoke script asserts `rel=canonical` and JSON-LD |
| `reviewed` must not be marketed as finished mapping | PARTIAL | PR #42 still open to harden map copy |
| GDPR consent-first analytics architecture documented | VERIFIED | `docs/REFERENCE_ARCHITECTURE.md` |

## 7. Open PR conflict analysis (#40 / #42 / #46)

- **#40**: replaces direct `main` pushes with `peter-evans/create-pull-request`; keeps hourly+daily crons relative to its base. Compatible intent with Issue #59. Needs token/permission verification and must be rebased onto current `main` (hourly cron currently missing on `main`).
- **#42**: search relevance, deep links, honest counts/map labels. Content-integrity PR; low conflict with steward publication changes; should remain independent.
- **#46**: adds `scripts/steward_schedule.py` and PR publication path; overlaps #40. Prefer one PR-publication design; do not merge incompatible dual systems. Reuse `steward_schedule.py` concepts in automation recovery PR.

## 8. Absolute baseline conclusions for execution

1. Restore hourly research schedule that #48 removed, without claiming that restores verified org promotions.
2. Stop direct-main automation commits via reviewed PR gate (#40 lineage).
3. Harden production smoke diagnostics for non-JSON bodies.
4. Use NYEOMSZSZ seeds as discovery inputs only; keep lifecycle gates.
5. Keep BGA on lawful import/blocker path — no scraping.
6. Do not mark countries complete from cycle progress or green Actions runs.

## 9. Rollback

This audit PR only adds documentation, seed/reconciliation JSON, adapter stub, and tests. Rollback = revert the PR commit; no canonical organization records are modified.
