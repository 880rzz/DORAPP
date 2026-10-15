#!/usr/bin/env python3
"""Daily press discovery for every eligible canonical organization; unverified queue only."""
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "global-press-review-queue.json"
MAX_WORKERS = 8
MAX_QUEUE = 2500
TIMEOUT = 12
UA = "DORAPP-PressDiscovery/1.0 (+https://www.diaszporaterkep.hu/)"

def read(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def eligible_organizations():
    rows = []
    for path in sorted((DATA / "countries").glob("*/organizations.json")):
        iso = path.parent.name
        for org in read(path, {}).get("organizations", []):
            name = str(org.get("name") or "").strip()
            if not (org.get("id") and name and org.get("entityClass") != "activity"):
                continue
            if org.get("status") in {"candidate", "unverified", "needs-review", "needs_review"}:
                continue
            if not org.get("website") or not org.get("profileVerifiedAt"):
                continue
            rows.append((iso, org["id"], name))
    return rows

def discover_one(organization):
    iso, entity_id, name = organization
    query = '"' + name.replace('"', "") + '" when:7d'
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({
        "q": query, "hl": "hu", "gl": "HU", "ceid": "HU:hu"
    })
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept":"application/rss+xml,application/xml,text/xml"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            xml = response.read(800000)
        root = ET.fromstring(xml)
        matches = []
        for item in root.findall("./channel/item")[:10]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            if not title or not link.startswith("https://"):
                continue
            matches.append({
                "country": iso, "organizationId": entity_id,
                "organizationName": name, "title": title, "url": link,
                "published": item.findtext("pubDate"),
                "status": "candidate-needs-identity-and-source-verification",
                "discoverySource": "Google News RSS",
            })
        return organization, matches, None
    except Exception as exc:
        return organization, [], type(exc).__name__

def main():
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    organizations = eligible_organizations()
    prior = read(OUT, {"candidates":[]})
    candidates = {
        (row.get("country"), row.get("organizationId"), row.get("url")): row
        for row in prior.get("candidates", []) if row.get("url")
    }
    checked = 0
    errors = []
    # Every eligible organization is attempted once per daily run. A bounded
    # worker pool prevents unbounded simultaneous external requests.
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(discover_one, organization) for organization in organizations]
        for future in as_completed(futures):
            org, found, error = future.result()
            iso, entity_id, _ = org
            if error:
                errors.append({"country":iso,"organizationId":entity_id,"error":error})
                continue
            checked += 1
            for item in found:
                key = (iso, entity_id, item["url"])
                if key not in candidates:
                    item["discoveredAt"] = now
                    candidates[key] = item
                else:
                    candidates[key]["lastSeenAt"] = now

    rows = sorted(
        candidates.values(),
        key=lambda item: (item.get("discoveredAt",""), item.get("country",""), item.get("organizationId",""), item.get("url","")),
        reverse=True
    )[:MAX_QUEUE]
    result = {
        "schemaVersion": 2,
        "lastRunAt": now,
        "organizationsTotal": len(organizations),
        "organizationsAttempted": len(organizations),
        "organizationsChecked": checked,
        "organizationsFailed": len(errors),
        "errors": sorted(errors, key=lambda x:(x["country"],x["organizationId"])),
        "candidates": rows,
        "publicationPolicy": "Discovery only. Verify publisher URL, exact identity, full article and relationship before publishing. Never infer endorsement or partnership.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Global daily press discovery: attempted={len(organizations)},"
        f" checked={checked}, failed={len(errors)}, queued={len(rows)}"
    )

if __name__ == "__main__":
    main()
