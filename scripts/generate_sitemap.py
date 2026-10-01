#!/usr/bin/env python3
import json
from pathlib import Path
from xml.sax.saxutils import escape
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
BASE="https://diaszpora.kozpontiszovetseg.at"
READY={"reviewed","verified-zero"}

org=json.loads((ROOT/"data/organizations.json").read_text(encoding="utf-8"))
edu=json.loads((ROOT/"data/education.json").read_text(encoding="utf-8"))
ev=json.loads((ROOT/"data/events.json").read_text(encoding="utf-8"))
globaldb=json.loads((ROOT/"data/global.json").read_text(encoding="utf-8"))

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
urls += [(f"{BASE}/esemenyek/{quote(x['id'])}.html",str(x.get("verifiedAt") or event_updated)[:10]) for x in ev.get("events",[])]
urls += [(f"{BASE}/tartomanyok/{x['id']}.html",org_updated) for x in org.get("states",[])]
urls += [(f"{BASE}/kategoriak/{x['id']}.html",org_updated) for x in org.get("categoryDefinitions",[])]

for c in globaldb.get("countries",[]):
    if c.get("researchStatus") not in READY:
        continue
    iso=c["iso2"]
    urls.append((f"{BASE}/countries/{iso}/",global_updated))

    op=ROOT/"data"/"countries"/iso/"organizations.json"
    if op.exists():
        try: odoc=json.loads(op.read_text(encoding="utf-8"))
        except Exception: odoc={}
        for o in odoc.get("organizations",odoc.get("items",[])):
            if o.get("id"):
                urls.append((f"{BASE}/countries/{iso}/organizations/{quote(str(o['id']))}.html",str(o.get("profileVerifiedAt") or global_updated)[:10]))

    ep=ROOT/"data"/"countries"/iso/"education.json"
    if ep.exists():
        try: edoc=json.loads(ep.read_text(encoding="utf-8"))
        except Exception: edoc={}
        for e in edoc.get("institutions",edoc.get("education",edoc.get("items",[]))):
            if e.get("id"):
                urls.append((f"{BASE}/countries/{iso}/education/{quote(str(e['id']))}.html",str(e.get("verifiedAt") or global_updated)[:10]))

    vp=ROOT/"data"/"countries"/iso/"events.json"
    if vp.exists():
        try: vdoc=json.loads(vp.read_text(encoding="utf-8"))
        except Exception: vdoc={}
        for e in vdoc.get("events",vdoc.get("items",[])):
            if e.get("id"):
                urls.append((f"{BASE}/countries/{iso}/events/{quote(str(e['id']))}.html",str(e.get("verifiedAt") or global_updated)[:10]))

seen=set()
dedup=[]
for item in urls:
    if item[0] in seen: continue
    seen.add(item[0]); dedup.append(item)

xml=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u,lastmod in dedup:
    extra=f"<lastmod>{escape(lastmod)}</lastmod>" if lastmod else ""
    xml.append(f"  <url><loc>{escape(u)}</loc>{extra}</url>")
xml.append("</urlset>")
(ROOT/"sitemap.xml").write_text("\n".join(xml)+"\n",encoding="utf-8")
print(f"sitemap_urls={len(dedup)}")
