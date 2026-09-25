#!/usr/bin/env python3
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]
BASE="https://diaszpora.kozpontiszovetseg.at"
org=json.loads((ROOT/"data/organizations.json").read_text(encoding="utf-8"))
edu=json.loads((ROOT/"data/education.json").read_text(encoding="utf-8"))
ev=json.loads((ROOT/"data/events.json").read_text(encoding="utf-8"))

org_updated=str(org.get("updated") or "")[:10]
edu_updated=str(edu.get("updated") or "")[:10]
event_updated=str(ev.get("updated") or "")[:10]
global_updated=max(x for x in (org_updated,edu_updated,event_updated) if x)

urls=[
    (f"{BASE}/",global_updated),
    (f"{BASE}/forrasok.html",global_updated),
    (f"{BASE}/llms.txt",global_updated),
    (f"{BASE}/ai.txt",global_updated),
    (f"{BASE}/adatminoseg.html",global_updated),
    (f"{BASE}/ai-entry.json",global_updated),
    (f"{BASE}/entity.jsonld",global_updated),
]
urls += [(f"{BASE}/szervezetek/{x['id']}.html",str(x.get("profileVerifiedAt") or org_updated)[:10]) for x in org.get("organizations",[])]
urls += [(f"{BASE}/oktatas/{x['id']}.html",edu_updated) for x in edu.get("institutions",[])]
urls += [(f"{BASE}/esemenyek/{x['id']}.html",str(x.get("verifiedAt") or event_updated)[:10]) for x in ev.get("events",[])]
urls += [(f"{BASE}/tartomanyok/{x['id']}.html",org_updated) for x in org.get("states",[])]
urls += [(f"{BASE}/kategoriak/{x['id']}.html",org_updated) for x in org.get("categoryDefinitions",[])]

xml=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u,lastmod in urls:
    extra=f"<lastmod>{escape(lastmod)}</lastmod>" if lastmod else ""
    xml.append(f"  <url><loc>{escape(u)}</loc>{extra}</url>")
xml.append("</urlset>")
(ROOT/"sitemap.xml").write_text("\n".join(xml)+"\n",encoding="utf-8")
print(f"sitemap_urls={len(urls)}")
