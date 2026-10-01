#!/usr/bin/env python3
"""Generate the compact global autocomplete index from reviewed country datasets."""
import json
import unicodedata
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

def norm(value):
    s = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(ch for ch in s if not unicodedata.combining(ch)).casefold().strip()

def entity_items(payload, keys):
    for key in keys:
        if isinstance(payload.get(key), list):
            return payload[key]
    return []

registry = read_json(DATA / "global.json", {"countries": []})
items = []
seen = set()

def add(item):
    key = (item.get("type"), item.get("country"), item.get("id") or norm(item.get("label")))
    if key in seen:
        return
    seen.add(key)
    item["search"] = norm(" ".join(str(v) for v in item.get("searchParts", []) if v))
    item.pop("searchParts", None)
    items.append(item)

for country in registry.get("countries", []):
    iso = country.get("iso2")
    if not iso:
        continue
    label = country_label(country)
    status = country.get("researchStatus", "unresearched")
    if status not in READY:
        continue

    route = country.get("route") or f"countries/{iso}/"
    add({
        "type": "country",
        "id": iso,
        "label": label,
        "country": iso,
        "countryLabel": label,
        "href": route,
        "searchParts": [label, iso, country.get("iso3"), *(country.get("name") or {}).values()],
    })

    base = DATA / "countries" / iso
    org_data = read_json(base / "organizations.json", {})
    edu_data = read_json(base / "education.json", {})
    event_data = read_json(base / "events.json", {})
    orgs = entity_items(org_data, ("organizations", "items"))
    edus = entity_items(edu_data, ("institutions", "education", "items"))
    events = entity_items(event_data, ("events", "items"))

    cities = {}
    activities = {}

    for org in orgs:
        if org.get("entityClass") == "activity":
            continue
        oid = org.get("id")
        name = org.get("name")
        if not oid or not name:
            continue
        city = org.get("city") or ""
        add({
            "type": "organization",
            "id": oid,
            "label": name,
            "country": iso,
            "countryLabel": label,
            "city": city,
            "meta": " · ".join(v for v in [city, org.get("type")] if v),
            "href": f"countries/{iso}/organizations/{quote(str(oid))}.html",
            "searchParts": [name, city, org.get("region"), org.get("type"), org.get("intro"), org.get("summary"), *(org.get("activities") or [])],
        })
        if city:
            cities[norm(city)] = city
        for activity in org.get("activities") or []:
            if activity:
                activities[norm(activity)] = str(activity)

    for edu in edus:
        eid = edu.get("id")
        name = edu.get("name")
        if not eid or not name:
            continue
        city = edu.get("city") or ""
        add({
            "type": "organization",
            "subtype": "education",
            "id": eid,
            "label": name,
            "country": iso,
            "countryLabel": label,
            "city": city,
            "meta": " · ".join(v for v in [city, edu.get("type")] if v),
            "href": f"countries/{iso}/education/{quote(str(eid))}.html",
            "searchParts": [name, city, edu.get("region"), edu.get("type"), edu.get("intro"), edu.get("summary")],
        })
        if city:
            cities[norm(city)] = city

    for event in events:
        eid = event.get("id")
        name = event.get("name") or event.get("title")
        city = event.get("city") or ""
        if city:
            cities[norm(city)] = city
        for activity in event.get("categories") or []:
            if activity:
                activities[norm(activity)] = str(activity)
        if eid and name:
            add({
                "type": "program",
                "id": eid,
                "label": name,
                "country": iso,
                "countryLabel": label,
                "city": city,
                "meta": " · ".join(v for v in [event.get("startDate") or event.get("date"), city, event.get("venue")] if v),
                "href": f"countries/{iso}/events/{quote(str(eid))}.html",
                "searchParts": [name, city, event.get("region"), event.get("venue"), event.get("organizer"), event.get("description"), *(event.get("categories") or [])],
            })

    for city in sorted(cities.values(), key=norm):
        add({
            "type": "city",
            "id": norm(city),
            "label": city,
            "country": iso,
            "countryLabel": label,
            "meta": label,
            "href": f"countries/{iso}/?city={quote(city)}",
            "searchParts": [city, label, iso],
        })

    for activity in sorted(activities.values(), key=norm):
        add({
            "type": "activity",
            "id": norm(activity),
            "label": activity,
            "country": iso,
            "countryLabel": label,
            "meta": label,
            "href": f"countries/{iso}/?q={quote(activity)}",
            "searchParts": [activity, label, iso],
        })

items.sort(key=lambda x: (norm(x.get("label")), x.get("type", ""), x.get("country", "")))
out = {
    "schemaVersion": 1,
    "readyStatuses": sorted(READY),
    "generatedFrom": "data/global.json + reviewed country datasets",
    "count": len(items),
    "items": items,
}
(DATA / "global-search-index.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(f"Global search index: {len(items)} items")
