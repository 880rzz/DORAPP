#!/usr/bin/env python3
"""Audit the daily DORAPP mirror of the canonical 29-member event catalogue.

Only dated, explicitly verified federation records count as imported events.
Social posts that lack independently verified event dates remain candidates.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime, date
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
MARKER = "ecosystem-member-programs"


def read(file):
    return json.loads((ROOT / file).read_text(encoding="utf-8"))


def date_part(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        raise ValueError("Invalid event date: " + str(value))


def report():
    sources = read("data/member-event-sources-ecosystem.json")
    programs = read("data/member-programs-ecosystem.json")
    events = read("data/events.json")["events"]
    organizations = {row["id"]: row for row in read("data/organizations.json")["organizations"]}
    if sources.get("sourceRepository") != "880rzz/okoszisztema" or programs.get("sourceRepository") != "880rzz/okoszisztema":
        raise ValueError("Federation mirrors do not identify canonical Ökoszisztéma authority")
    members = sources.get("members", [])
    if len(members) != 29 or sources.get("organizationCount") != 29 or len({m["memberId"] for m in members}) != 29:
        raise ValueError("Expected 29 distinct association source mappings")
    if sources.get("sourceCount") != sum(len(m.get("calendarSources", [])) for m in members):
        raise ValueError("Source count mismatch")
    by_id = {}
    for m in members:
        oid = m["organizerId"]
        org = organizations.get(oid)
        if not org or not any(x.get("umbrellaId") == "kozponti-szovetseg" for x in org.get("memberships", [])):
            raise ValueError("Missing valid association mapping: " + oid)
        if org.get("calendarSources") != m["calendarSources"] or org.get("eventSources") != m["eventSources"]:
            raise ValueError("DORAPP source list differs from canonical mirror: " + oid)
        by_id[m["memberId"]] = m
    today = datetime.now(ZoneInfo("Europe/Vienna")).date()
    canonical_events = {}
    current = Counter()
    total = Counter()
    for event in programs.get("verifiedEvents", []):
        if event.get("verificationStatus") != "verified" or not event.get("verifiedAt"):
            raise ValueError("Unverified source in canonical verifiedEvents")
        if event.get("id") in canonical_events:
            raise ValueError("Duplicate member event ID")
        member = by_id.get(event.get("memberId"))
        if not member or event.get("organizerId") != member["organizerId"]:
            raise ValueError("Wrong member association for: " + str(event.get("id")))
        canonical_events[event["id"]] = event
        total[member["memberId"]] += 1
        if date_part(event.get("endDate") or event.get("startDate")) >= today and event.get("eventStatus") != "https://schema.org/EventCancelled":
            current[member["memberId"]] += 1
    actual = {row["id"]: row for row in events if row.get("sourceType") == MARKER}
    missing = []
    for event_id, source in canonical_events.items():
        row = actual.get(event_id)
        if not row or row.get("organizationId") != source["organizerId"] or row.get("startDate") != source["startDate"] or row.get("sourceUrl") != source["sourceUrl"]:
            missing.append(event_id)
    if missing:
        raise ValueError("Canonical verified member events not reflected in DORAPP events.json: " + ", ".join(missing[:6]))
    unknown = set(actual) - set(canonical_events)
    if unknown:
        raise ValueError("Stale imported member events remain after sync: " + ", ".join(sorted(unknown)[:6]))
    for candidate in programs.get("programCandidates", []):
        if candidate.get("status") != "date-unverified" or candidate.get("startDate"):
            raise ValueError("Unverified candidate promoted with a date")
    now = datetime.now(ZoneInfo("Europe/Vienna"))
    return {
        "schemaVersion": 1,
        "generatedAt": now.isoformat(),
        "authority": "880rzz/okoszisztema",
        "status": "source-and-program-mirrors-consistent",
        "sourceCounts": {
            "members": len(members),
            "registeredSources": sources["sourceCount"],
            "automaticallyEligible": sum(s.get("ingestEvents") is True for m in members for s in m["calendarSources"]),
        },
        "programCounts": {
            "verified": len(canonical_events),
            "importedToDorapp": len(actual),
            "unverifiedDateCandidates": len(programs.get("programCandidates", [])),
            "associationsWithCurrentDated": sum(bool(current[m["memberId"]]) for m in members),
            "associationsWithoutCurrentDated": [m["memberId"] for m in members if not current[m["memberId"]]],
        },
        "note": "This verifies canonical-sync integrity, not completeness of third-party calendars. Social sources cannot be guaranteed accessible by public automated clients.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = report()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts, programs = data["sourceCounts"], data["programCounts"]
    line = (f"Mirrors agree: {counts['members']} associations, {counts['registeredSources']} source URLs, "
            f"{counts['automaticallyEligible']} automatic feeds; {programs['importedToDorapp']} imported, "
            f"{programs['associationsWithCurrentDated']} associations with current dated programs.")
    print(line)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("## DÖR / Ökoszisztéma — napi tagszervezeti forrásszinkron\n\n" + line + "\n\n")
            f.write("A Facebook/Instagram források külön szerkesztői ellenőrzést igényelnek.\n")


if __name__ == "__main__":
    main()
