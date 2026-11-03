# Evidence lifecycle architecture (PR C) — 2026-11-03

## Goal

Keep DORAPP’s canonical `data/countries/<iso2>/*.json` architecture while adding an explicit evidence and review gate so discovery cannot auto-publish.

## Lifecycle

`DISCOVERED → QUALIFIED → FIRST_PARTY_CHECKED → HUMAN_REVIEWED → PUBLISHABLE → PUBLISHED`

Side states: `REJECTED`, `STALE`, `DISPUTED`, `NEEDS_REVIEW`.

Implemented in `scripts/evidence_lifecycle.py` with enforced transition rules.

## Identity

- Stable public `id` values are preserved by `scripts/entity_resolution.py`.
- Dedup keys: official website host+normalized URL, or normalized name+city inside the same ISO country.
- Cross-border IE/GB name collisions do not merge when `country` differs.

## Claims and relationships

Claims store statement + sources + timestamps + strength (`observed|corroborated|first_party|human_confirmed`).

Relationship types include membership, funding award/unsuccessful application, press mention, calendar source, institutional parent. Funding is never membership.

## Hard gates

- Secondary directory/press/wikipedia/social sources alone cannot justify publishable verification.
- NYEOMSZSZ directory listing alone remains at most `DISCOVERED` / membership `disputed|current-candidate`.
- BGA grant rows remain funding evidence only.

## Migration / rollback

This PR introduces helpers, docs, and fixtures only. No canonical organization records are rewritten. Rollback = revert the PR.
