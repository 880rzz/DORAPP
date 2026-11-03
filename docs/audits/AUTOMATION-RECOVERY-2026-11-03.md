# Automation recovery notes (PR B) — 2026-11-03

## Root causes addressed

1. **Hourly cron missing on `main`**
   - #37/#41 restored hourly research.
   - #48 commit explicitly switched to daily-only (`fix(automation): run global research daily rather than hourly`).
   - This PR restores `37 0-1,3-23 * * *` plus daily `37 2 * * *`.

2. **Direct pushes to `main`**
   - Global steward, static build, Austria curator, education audit, and taxonomy audit used `git push origin HEAD:main`.
   - Replaced with `peter-evans/create-pull-request@v7` reviewed PR branches:
     - `automation/diaspora-research`
     - `automation/generated-static`
     - `automation/austria-program-curator`
     - `automation/education-site-audit`
     - `automation/taxonomy-audit`

3. **Production smoke ES invalid JSON**
   - Historical failure: Actions run `41452864144` (`es: invalid JSON`).
   - Live file on 2026-11-03 parses as valid JSON with `organizations`.
   - Smoke now classifies HTML/empty/404/invalid-json/unexpected-shape separately via `scripts/production_json_probe.py`.

## Operational prerequisites

- Enable Actions permission: **Allow GitHub Actions to create and approve pull requests**, or set `DORAPP_PR_TOKEN`.
- Prefer a PAT so automation-created PRs still trigger `Validate DORAPP`.
- Branch protection should require validation before merge. No auto-merge.

## Validate runner pin

GitHub `ubuntu-latest` began resolving to Ubuntu 26.04, which Playwright `1.55.0` cannot provision (`ERROR: Playwright does not support chromium on ubuntu26.04-x64`). `validate.yml` is pinned to `ubuntu-24.04` and Playwright is bumped to `1.56.1` so unit/global gates are not blocked by browser dependency install.

## Semantics preserved

- Successful steward run ≠ verified organization.
- Daily event/press refresh is independent and driven by `scripts/steward_schedule.py`.
- Missed hourly research emits a workflow warning when `research-state.lastRunAt` is >2h old.
