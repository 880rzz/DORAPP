#!/usr/bin/env python3
"""Generate a global future-event calendar from reviewed country datasets."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
READY = {"reviewed", "verified-zero"}

def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def country_label(country):
    names = country.get("name") or {}
    return names.get("hu") or names.get("en") or str(country.get("iso2", "")).upper()

def parse_start(value):
    if not value:
        return None
    raw = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except Exception:
        try:
            dt = datetime.fromisoformat(raw[:10] + "T00:00:00+00:00")
        except Exception:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

registry = read_json(DATA / "global.json", {"countries": []})
now = datetime.now(timezone.utc)
events = []

for country in registry.get("countries", []):
    iso = country.get("iso2")
    if not iso or country.get("researchStatus") not in READY:
        continue
    label = country_label(country)
    payload = read_json(DATA / "countries" / iso / "events.json", {})
    for event in payload.get("events", payload.get("items", [])):
        start_raw = event.get("startDate") or event.get("date")
        start = parse_start(start_raw)
        end = parse_start(event.get("endDate"))
        if start is None or (end or start) < now:
            continue
        eid = event.get("id")
        name = event.get("name") or event.get("title")
        if not eid or not name:
            continue
        events.append({
            "id": eid,
            "country": iso,
            "countryLabel": label,
            "name": name,
            "startDate": start_raw,
            "endDate": event.get("endDate"),
            "city": event.get("city"),
            "region": event.get("region"),
            "venue": event.get("venue"),
            "organizer": event.get("organizer"),
            "organizerId": event.get("organizerId") or event.get("organizationId"),
            "categories": event.get("categories") or [],
            "sourceUrl": event.get("sourceUrl"),
            "href": f"countries/{iso}/events/{quote(str(eid))}.html",
        })

events.sort(key=lambda e: (str(e.get("startDate") or ""), str(e.get("countryLabel") or ""), str(e.get("name") or "")))
out = {
    "schemaVersion": 1,
    "generatedAt": now.isoformat(),
    "readyStatuses": sorted(READY),
    "count": len(events),
    "events": events,
}
(DATA / "global-events.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Global future events: {len(events)}")
