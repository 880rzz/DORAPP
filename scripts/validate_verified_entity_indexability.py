#!/usr/bin/env python3
"""Every verified canonical diaspora organization must be discoverable and indexable."""
import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BASE = "https://www.diaszporaterkep.hu"
TRUSTED = {"official", "government", "institutional", "registry"}
REVIEWED = {"reviewed", "verified-zero"}
NOT_PUBLIC = {"candidate", "unverified", "needs-review", "needs_review"}

def read(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def eligible(organization, country_reviewed):
    if not organization.get("id") or organization.get("entityClass") == "activity":
        return False
    if organization.get("status") in NOT_PUBLIC:
        return False
    if country_reviewed:
        return True
    return bool(organization.get("profileVerifiedAt") and any(
        isinstance(source, dict) and source.get("url") and source.get("type") in TRUSTED
        for source in (organization.get("evidenceSources") or [])
    ))

registry = read(DATA/"global.json", {"countries":[]})
search = read(DATA/"global-search-index.json", {"items":[]})
indexed = {
    (item.get("country"), item.get("id"))
    for item in search.get("items", [])
    if item.get("type") == "organization" and item.get("subtype") != "education"
}
sitemap = (ROOT/"sitemap.xml").read_text(encoding="utf-8")
errors = []
count = 0
for country in registry.get("countries", []):
    iso = country.get("iso2")
    reviewed = country.get("researchStatus") in REVIEWED
    doc = read(DATA/"countries"/iso/"organizations.json", {"organizations":[]})
    for org in doc.get("organizations", doc.get("items", [])):
        if not eligible(org, reviewed):
            continue
        eid = str(org["id"])
        url = f"{BASE}/countries/{iso}/organizations/{quote(eid)}.html"
        route = ROOT/"countries"/iso/"organizations"/f"{eid}.html"
        count += 1
        if not route.is_file():
            errors.append(f"{iso}/{eid}: missing generated profile page")
        if url not in sitemap:
            errors.append(f"{iso}/{eid}: missing canonical sitemap entry")
        if (iso, org["id"]) not in indexed:
            errors.append(f"{iso}/{eid}: missing global search index entry")
if errors:
    print("\n".join("ERROR: " + error for error in errors))
    sys.exit(1)
print(f"Verified global entity indexability OK: {count} organizations")
