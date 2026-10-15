#!/usr/bin/env python3
"""Discover potential global press mentions. Queue only; never publish unverified matches."""
import json, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "global-press-review-queue.json"
MAX_ORGS = 24
UA = "DORAPP-PressDiscovery/1.0 (+https://www.diaszporaterkep.hu/)"

def read(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def main():
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    countries = sorted((DATA / "countries").glob("*/organizations.json"))
    orgs = []
    for path in countries:
        for org in read(path, {}).get("organizations", []):
            name = str(org.get("name") or "").strip()
            if org.get("id") and len(name) >= 12 and org.get("website") and org.get("entityClass") != "activity":
                orgs.append((path.parent.name, org["id"], name))
    prior = read(OUT, {"candidates": [], "cursor": 0})
    cursor = int(prior.get("cursor", 0)) % max(1, len(orgs))
    candidates = { (c.get("country"), c.get("organizationId"), c.get("url")): c for c in prior.get("candidates", []) if c.get("url") }
    checked = 0
    errors = []
    for i in range(min(MAX_ORGS, len(orgs))):
        iso, eid, name = orgs[(cursor + i) % len(orgs)]
        query = '"' + name + '" when:7d'
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q":query,"hl":"hu","gl":"HU","ceid":"HU:hu"})
        try:
            req = urllib.request.Request(url, headers={"User-Agent":UA})
            with urllib.request.urlopen(req, timeout=12) as resp:
                xml = resp.read(800000)
            root = ET.fromstring(xml)
            for item in root.findall("./channel/item")[:10]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if not title or not link.startswith("https://"):
                    continue
                key = (iso, eid, link)
                if key not in candidates:
                    candidates[key] = {"country":iso,"organizationId":eid,"organizationName":name,"title":title,"url":link,"published":item.findtext("pubDate"),"discoveredAt":now,"status":"candidate-needs-identity-and-source-verification","discoverySource":"Google News RSS"}
            checked += 1
        except Exception as exc:
            errors.append({"country":iso,"organizationId":eid,"error":type(exc).__name__})
    # Bound queue size, preserve pending candidates and never infer endorsement.
    rows = sorted(candidates.values(), key=lambda c:c.get("discoveredAt",""), reverse=True)[:2500]
    result = {"schemaVersion":1,"lastRunAt":now,"cursor":(cursor + min(MAX_ORGS,len(orgs))) % max(1,len(orgs)),"organizationsTotal":len(orgs),"organizationsChecked":checked,"errors":errors,"candidates":rows,"publicationPolicy":"Discovery only. Verify exact identity, article content, independent source and relationship before adding to pressMentions."}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Global press discovery: checked {checked}/{len(orgs)} organizations; queued {len(rows)} candidates; {len(errors)} errors")

if __name__ == "__main__":
    main()
