#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE="https://diaszpora.kozpontiszovetseg.at"
org=json.loads((ROOT/"data/organizations.json").read_text(encoding="utf-8"))
edu=json.loads((ROOT/"data/education.json").read_text(encoding="utf-8"))
ev=json.loads((ROOT/"data/events.json").read_text(encoding="utf-8"))
sitemap=(ROOT/"sitemap.xml").read_text(encoding="utf-8")
errors=[]

def check_page(path,canonical,entity_id=None):
    p=ROOT/path
    if not p.exists():
        errors.append(f"missing generated page: {path}")
        return
    text=p.read_text(encoding="utf-8")
    if f'<link rel="canonical" href="{canonical}">' not in text:
        errors.append(f"canonical mismatch: {path}")
    if f'<meta name="robots" content="index,follow' not in text:
        errors.append(f"robots meta missing: {path}")
    if canonical not in sitemap:
        errors.append(f"sitemap missing: {canonical}")
    blocks=re.findall(r'<script type="application/ld\+json">(.*?)</script>',text,re.S)
    if not blocks:
        errors.append(f"json-ld missing: {path}")
        return
    try:
        payload=json.loads(blocks[0].replace("<\\/","</"))
    except Exception as ex:
        errors.append(f"invalid json-ld: {path} -> {ex}")
        return
    graph=payload.get("@graph",[]) if isinstance(payload,dict) else []
    ids={x.get("@id") for x in graph if isinstance(x,dict)}
    if canonical+"#page" not in ids:
        errors.append(f"page schema id mismatch: {path}")
    if entity_id and entity_id not in ids:
        errors.append(f"entity schema id mismatch: {path}")

for x in org.get("organizations",[]):
    url=f'{BASE}/szervezetek/{x["id"]}.html'
    check_page(f'szervezetek/{x["id"]}.html',url,url+"#organization")
for x in edu.get("institutions",[]):
    url=f'{BASE}/oktatas/{x["id"]}.html'
    check_page(f'oktatas/{x["id"]}.html',url,url+"#education")
for x in ev.get("events",[]):
    url=f'{BASE}/esemenyek/{x["id"]}.html'
    check_page(f'esemenyek/{x["id"]}.html',url,url+"#event")

for p in ("llms.txt","ai.txt","ai-entry.json","entity.jsonld","robots.txt","sitemap.xml","forrasok.html","adatminoseg.html"):
    if not (ROOT/p).exists(): errors.append(f"missing trust/search artifact: {p}")

print(f"static_output organizations={len(org.get('organizations',[]))} education={len(edu.get('institutions',[]))} events={len(ev.get('events',[]))}")
if errors:
    print("\n".join("ERROR: "+x for x in errors))
    sys.exit(1)
