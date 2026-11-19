#!/usr/bin/env python3
"""Mirror federation member programs from the Ökoszisztéma authority.

Only explicitly verified, dated events enter the DORAPP event calendar.
Undated social announcements remain in the separate source-discovery registry.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE = DATA / "member-programs-ecosystem.json"
EVENTS = DATA / "events.json"
ORGS = DATA / "organizations.json"
SOURCE = "https://raw.githubusercontent.com/880rzz/okoszisztema/main/data/member-programs.json"
MARKER = "ecosystem-member-programs"


def https_url(value):
    u = urlparse(str(value or ""))
    return u.scheme == "https" and bool(u.netloc)


def valid_date(value):
    if not isinstance(value, str) or not value:
        return False
    try:
        return bool(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except (ValueError, TypeError):
        return False


def validate_registry(payload):
    if not isinstance(payload, dict) or payload.get("schemaVersion") != 1:
        raise ValueError("Unsupported member program schema")
    if payload.get("sourceRepository") != "880rzz/okoszisztema":
        raise ValueError("Member program source ownership mismatch")
    if not isinstance(payload.get("programCandidates"), list) or not isinstance(payload.get("verifiedEvents"), list):
        raise ValueError("Missing candidate / verified event arrays")
    seen = set()
    for entry in payload["programCandidates"]:
        if not isinstance(entry, dict) or not entry.get("id") or entry["id"] in seen:
            raise ValueError("Missing or duplicate candidate ID")
        seen.add(entry["id"])
        if entry.get("status") != "date-unverified" or not entry.get("memberId") or not entry.get("organizerId") or not entry.get("title"):
            raise ValueError("Invalid unverified candidate")
        if entry.get("startDate") or entry.get("endDate") or not https_url(entry.get("sourceUrl")):
            raise ValueError("Candidate cannot assert a date or use a non-HTTPS source")
    for entry in payload["verifiedEvents"]:
        if not isinstance(entry, dict) or entry.get("verificationStatus") != "verified":
            raise ValueError("Only verified member events may be imported")
        for required in ("id", "memberId", "organizerId", "name", "startDate", "sourceUrl", "verifiedAt"):
            if not entry.get(required):
                raise ValueError("Verified event missing " + required)
        if entry["id"] in seen:
            raise ValueError("Duplicate program ID")
        seen.add(entry["id"])
        if not valid_date(entry["startDate"]) or (entry.get("endDate") and not valid_date(entry["endDate"])):
            raise ValueError("Malformed verified event date")
        if not https_url(entry["sourceUrl"]) or not valid_date(entry["verifiedAt"]):
            raise ValueError("Verified event missing valid evidence")
    return payload


def event_records(payload, organizations):
    output = []
    for entry in payload["verifiedEvents"]:
        org = organizations.get(entry["organizerId"])
        if not org or not any(x.get("umbrellaId") == "kozponti-szovetseg" for x in org.get("memberships", [])):
            raise ValueError("Verified event organizer is not a federation member: " + entry["organizerId"])
        if entry.get("eventStatus") == "https://schema.org/EventCancelled":
            continue
        output.append({
            "id": entry["id"],
            "organizationId": entry["organizerId"],
            "name": entry["name"],
            "organizer": org["name"],
            "state": org["state"],
            "city": org["city"],
            "venue": entry.get("venue") or "",
            "address": entry.get("address") or "",
            "startDate": entry["startDate"],
            "endDate": entry.get("endDate") or "",
            "description": entry.get("description") or "",
            "sourceUrl": entry["sourceUrl"],
            "verifiedAt": entry["verifiedAt"],
            "eventStatus": entry.get("eventStatus") or "https://schema.org/EventScheduled",
            "attendanceMode": entry.get("attendanceMode") or "https://schema.org/OfflineEventAttendanceMode",
            "registrationUrl": entry.get("registrationUrl"),
            "price": entry.get("price"),
            "priceCurrency": entry.get("priceCurrency"),
            "performers": entry.get("performers") or [],
            "audience": entry.get("audience"),
            "image": entry.get("image"),
            "programCategories": entry.get("programCategories") or ["kozosseg"],
            "sourceType": MARKER,
            "authoritySource": payload["authority"],
        })
    return output


def load_registry(offline=False):
    if offline:
        return validate_registry(json.loads(CACHE.read_text(encoding="utf-8")))
    try:
        req = Request(SOURCE, headers={"User-Agent": "DORAPP-federation-source-sync/1.0", "Accept": "application/json"})
        with urlopen(req, timeout=12) as response:
            payload = json.load(response)
        return validate_registry(payload)
    except Exception as exc:
        if not CACHE.exists():
            raise
        print("WARN: federation source unavailable; using last validated local mirror:", str(exc), file=sys.stderr)
        return validate_registry(json.loads(CACHE.read_text(encoding="utf-8")))


def sync(payload):
    source_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if not CACHE.exists() or CACHE.read_text(encoding="utf-8") != source_text:
        CACHE.write_text(source_text, encoding="utf-8")
    orgs = {x["id"]: x for x in json.loads(ORGS.read_text(encoding="utf-8"))["organizations"]}
    imported = event_records(payload, orgs)
    doc = json.loads(EVENTS.read_text(encoding="utf-8"))
    previous = doc["events"]
    canonical_ids = {e["id"] for e in imported}
    for e in previous:
        if e["id"] in canonical_ids and e.get("sourceType") != MARKER:
            raise ValueError("Program ID collision with independent DORAPP event: " + e["id"])
    new_events = [e for e in previous if e.get("sourceType") != MARKER] + imported
    if new_events != previous:
        doc["events"] = sorted(new_events, key=lambda e: (str(e.get("startDate", "")), str(e.get("id", ""))))
        doc["updated"] = datetime.now().astimezone().isoformat()
        EVENTS.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Federation source synced: %d pending leads; %d verified events" %
          (len(payload["programCandidates"]), len(imported)))


if __name__ == "__main__":
    sync(load_registry("--offline" in sys.argv))
