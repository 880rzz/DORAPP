# DORAPP Global Daily Steward — dailywork.md

## Purpose
Run daily across the complete global Hungarian diaspora platform to keep organization information, education data, source health and event calendars current.

## Safe start
Read current main HEAD, global country registry and workflow state. Process deterministic resumable country batches. Before every write re-read HEAD and target state; rebase rather than overwrite newer work.

## Every active country
For every researching, partial or reviewed country: validate official websites/public channels; check every calendarSources entry; refresh ingestEvents:true sources; discover future events; update changed dates, venues, registration URLs and cancellations only from evidence; expire events from future views while preserving provenance; refresh source health; check official contact/social changes; check umbrella/member directories; check education changes; update profileVerifiedAt only after actual verification.

## Event integrity
Never invent dates, organizer, venue or registration URL. Deduplicate by normalized organizer/name/date/source semantics. Never ingest discovery-only sources. Never attribute member events from aggregate calendars to the umbrella. Cancellation/postponement requires evidence. Preserve source URL and verification timestamp.

## Freshness escalation
Run deeper research when an official site disappears/redirects unrelated, social is deleted/renamed, a normally active calendar is anomalously stale, closure/merger/name change is announced, first-party contacts conflict, or country-wide discovery is overdue. 403/429/timeout is technical source health, not automatic deletion.

## Global discovery rotation
Event freshness runs for all active countries daily. Broader missing-organization discovery rotates with bounded workload, prioritizing unresearched countries, oldest broad review, known high Hungarian population with sparse coverage, then unresolved source/profile gaps. Search in local language, Hungarian and English.

## Global integrity
Rebuild derived country organization/event/education counts; verify world-map counts and country routes; rebuild global search indexes; detect duplicate canonical domains/social IDs across countries; review cross-border chapters as relationships rather than accidental duplicates; rebuild sitemap index/country sitemaps; validate JSON-LD/entity graph, robots, llms.txt and ai.txt.
Required invariants: legacy-only event sources = 0; authority conflicts = 0; orphan events = 0; broken country IDs = 0; hand-entered derived counts = 0.

## Commit and deploy
Commit only source-backed or deterministic generated changes. Avoid noise commits. Run validators; inspect exact failing job/step/log and fix root cause. Deploy, then verify global homepage, affected countries, search/event output and latest production SHA. Superseded cancelled runs are not defects.

## Daily run record
Persist timestamp, countries attempted/completed/failed, sources checked, health changes, organizations added/updated/flagged, events added/updated/cancelled/expired, education changes, unresolved conflicts, validation/deploy result and production SHA. Notify a human only when a genuine decision is required or production cannot be automatically restored.
