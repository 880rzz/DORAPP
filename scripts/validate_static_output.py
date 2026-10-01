#!/usr/bin/env python3
import json,re,sys
from urllib.parse import quote
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE="https://diaszpora.kozpontiszovetseg.at"
org=json.loads((ROOT/"data/organizations.json").read_text(encoding="utf-8"))
edu=json.loads((ROOT/"data/education.json").read_text(encoding="utf-8"))
ev=json.loads((ROOT/"data/events.json").read_text(encoding="utf-8"))
globaldb=json.loads((ROOT/"data/global.json").read_text(encoding="utf-8"))
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
    if "googletagmanager.com/gtag/js" in text or "gtag('config','G-1FC22JEX2F')" in text:
        errors.append(f"non-consent analytics bootstrap present: {path}")
    if "ui.js" not in text:
        errors.append(f"shared consent/navigation controller missing: {path}")
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
    encoded=quote(x["id"])
    url=f'{BASE}/esemenyek/{encoded}.html'
    check_page(f'esemenyek/{x["id"]}.html',url,url+"#event")

expected_event_pages={f'{x["id"]}.html' for x in ev.get("events",[])}
for path in (ROOT/"esemenyek").glob("*.html"):
    if path.name not in expected_event_pages:
        errors.append(f"stale generated event page: esemenyek/{path.name}")

for country in globaldb.get("countries",[]):
    iso=country["iso2"]
    path=ROOT/"countries"/iso/"index.html"
    canonical=f"{BASE}/countries/{iso}/"
    if not path.exists():
        errors.append(f"missing generated country page: countries/{iso}/index.html")
        continue
    text=path.read_text(encoding="utf-8")
    if f'<link rel="canonical" href="{canonical}">' not in text: errors.append(f"canonical mismatch: countries/{iso}/index.html")
    ready=country.get("researchStatus") in {"reviewed","verified-zero"}
    expected_robots='index,follow' if ready else 'noindex,follow'
    if f'<meta name="robots" content="{expected_robots}"' not in text: errors.append(f"robots meta mismatch: countries/{iso}/index.html")
    if "googletagmanager.com/gtag/js" in text: errors.append(f"non-consent analytics bootstrap present: countries/{iso}/index.html")
    if "ui.js" not in text: errors.append(f"shared consent/navigation controller missing: countries/{iso}/index.html")
    if 'id="terkep"' not in text or "country-map-board" not in text:
        errors.append(f"country territorial map missing: countries/{iso}/index.html")
    data_dir=ROOT/"data"/"countries"/iso
    has_country_data=False
    for data_name, keys in (("organizations.json",("organizations","items")),("education.json",("institutions","education","items")),("events.json",("events","items"))):
        dp=data_dir/data_name
        if not dp.exists(): continue
        doc=json.loads(dp.read_text(encoding="utf-8"))
        if any(isinstance(doc.get(k),list) and doc.get(k) for k in keys):
            has_country_data=True
    if has_country_data:
        for token in ('id="kereso"','id="countryOrgGrid"','id="countryEducationGrid"','id="countryEventGrid"',"country.js"):
            if token not in text: errors.append(f"Austria-parity country component missing ({token}): countries/{iso}/index.html")
    if ready and canonical not in sitemap: errors.append(f"sitemap missing: {canonical}")
    if not ready and canonical in sitemap: errors.append(f"unfinished country leaked into sitemap: {canonical}")
    blocks=re.findall(r'<script type="application/ld\+json">(.*?)</script>',text,re.S)
    try:
        payload=json.loads(blocks[0])
        if payload.get("@type")!="CollectionPage" or payload.get("url")!=canonical:
            errors.append(f"country schema mismatch: countries/{iso}/index.html")
    except Exception as ex:
        errors.append(f"invalid country json-ld: countries/{iso}/index.html -> {ex}")

for country in globaldb.get("countries",[]):
    iso=country["iso2"]
    org_path=ROOT/"data"/"countries"/iso/"organizations.json"
    if not org_path.exists(): continue
    odoc=json.loads(org_path.read_text(encoding="utf-8"))
    for item in odoc.get("organizations",odoc.get("items",[])):
        if item.get("entityClass")=="activity" or not item.get("id"): continue
        profile=ROOT/"countries"/iso/"organizations"/f"{item['id']}.html"
        if not profile.exists(): continue
        profile_text=profile.read_text(encoding="utf-8")
        for token in ("Kapcsolati háló","Hova töltik fel az eseményeiket?","Közösségi oldalak és nyilvános csatornák","Ellenőrző források"):
            if token not in profile_text:
                errors.append(f"rich organization profile layer missing ({token}): {iso}/{item['id']}")

for p in ("llms.txt","ai.txt","ai-entry.json","entity.jsonld","robots.txt","sitemap.xml","forrasok.html","adatminoseg.html","ui.js","world.js","country.js","data/global-search-index.json","data/global-events.json"):
    if not (ROOT/p).exists(): errors.append(f"missing trust/search artifact: {p}")

for p in ("index.html","forrasok.html","szervezet.html"):
    text=(ROOT/p).read_text(encoding="utf-8")
    if "googletagmanager.com/gtag/js" in text or "gtag('config','G-1FC22JEX2F')" in text:
        errors.append(f"non-consent analytics bootstrap present: {p}")
    if "ui.js" not in text:
        errors.append(f"shared consent/navigation controller missing: {p}")


country_js = (ROOT / "country.js").read_text(encoding="utf-8")
for token in ("pointerdown", "pointermove", "pointerup", "pointercancel", "setPointerCapture", "scale", "translate3d", "data-country-map-reset", "clamp"):
    if token not in country_js: errors.append(f"country map pan/zoom regression: missing {token}")
for iso in ("at", "nl", "be", "us"):
    page = (ROOT / "countries" / iso / "index.html").read_text(encoding="utf-8")
    if 'country-map-viewport' not in page or 'data-country-map-zoom-in' not in page: errors.append(f"{iso}: shared country map controller markup missing")
    if 'id="kereso"' in page and page.index('id="kereso"') > page.index('id="terkep"'): errors.append(f"{iso}: search must remain above map")

print(f"static_output organizations={len(org.get('organizations',[]))} education={len(edu.get('institutions',[]))} events={len(ev.get('events',[]))}")
if errors:
    print("\n".join("ERROR: "+x for x in errors))
    sys.exit(1)
