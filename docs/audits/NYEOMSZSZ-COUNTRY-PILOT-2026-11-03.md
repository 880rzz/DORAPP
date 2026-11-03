# NYEOMSZSZ country research pilot (PR D) — 2026-11-03

## Pilot batch

AT, ES, NL, FI — representative mix of reviewed / partial / unresearched states.

## What this PR does

- Creates evidence-backed coverage assessments under `data/nyeomszsz/coverage/`.
- Records umbrella seed linkage to NYEOMSZSZ directory/country pages.
- Probes first-party website HTTP availability where listed.
- Explicitly refuses `countryComplete=true`.

## What this PR does not do

- Does not invent organizations, addresses, membership edges, or contacts.
- Does not publish MADACH or Finnországi Magyarok Egyesülete into canonical country JSON.
- Does not mark reviewed countries as finished NYEOMSZSZ network maps.

## Observed anchors

| ISO | Canonical umbrella already present? | Seed website HTTP |
| --- | --- | --- |
| AT | yes (`kozponti-szovetseg`) | 200 kozpontiszovetseg.at |
| NL | yes (`hollandiai-magyar-szovetseg`) | first-party URL already canonical |
| ES | no MADACH org leaf yet (media boletin only) | 200 madach.es |
| FI | no organizations.json | 200 magyarutca.org |

## Next batch candidates

SE (SMOSZ already canonical), NO (nufo.no live, no country file), DE/BUOD, CZ, BA/IE/MK disputed membership set.
