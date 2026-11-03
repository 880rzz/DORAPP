# Automation recovery notes (PR B) — 2026-11-03

## Root causes addressed

1. **Hourly cron missing on `main`**
   - #37/#41 restored hourly research.
   - #48 commit explicitly switched to daily-only (`fix(automation): run global research daily rather than hourly`).
   - This PR restores `37 0-1,3-23 * * *` plus daily `37 2 * * *`.

2. **Direct pushes to `main`**
   - Global steward and static build used `git push origin HEAD:main`.
   - Replaced with `peter-evans/create-pull-request@v7` reviewed PR branches:
     - `automation/diaspora-research`
     - `automation/generated-static`

3. **Production smoke ES invalid JSON**
   - Historical failure: Actions run `41452864144` (`es: invalid JSON`).
   - Live file on 2026-11-03 parses as valid JSON with `organizations`.
   - Smoke now classifies HTML/empty/404/invalid-json/unexpected-shape separately via `scripts/production_json_probe.py`.

## Operational prerequisites

- Enable Actions permission: **Allow GitHub Actions to create and approve pull requests**, or set `DORAPP_PR_TOKEN`.
- Prefer a PAT so automation-created PRs still trigger `Validate DORAPP`.
- Branch protection should require validation before merge. No auto-merge.

## Semantics preserved

- Successful steward run ≠ verified organization.
- Daily event/press refresh is independent and driven by `scripts/steward_schedule.py`.
- Missed hourly research emits a workflow warning when `research-state.lastRunAt` is >2h old.
