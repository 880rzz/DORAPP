#!/usr/bin/env python3
import json,re,sys
from urllib.parse import quote
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE="https://www.diaszporaterkep.hu"
org=json.loads((ROOT/"data/organizations.json").read_text(encoding="utf-8"))
edu=json.loads((ROOT/"data/education.json").read_text(encoding="utf-8"))
ev=json.loads((ROOT/"data/events.json").read_text(encoding="utf-8"))
globaldb=json.loads((ROOT/"data/global.json").read_text(encoding="utf-8"))
global_search=json.loads((ROOT/"data/global-search-index.json").read_text(encoding="utf-8"))
sitemap=(ROOT/"sitemap.xml").read_text(encoding="utf-8")
errors=[]
OLD_BASE="https://diaszpora.kozpontiszovetseg.at"

public_files=[
    ROOT/"index.html", ROOT/"forrasok.html", ROOT/"szervezet.html",
    ROOT/"ai.txt", ROOT/"llms.txt", ROOT/"robots.txt", ROOT/"sitemap.xml",
    ROOT/"entity.jsonld", ROOT/"ai-entry.json",
]
public_files.extend(ROOT.rglob("*.html"))
for path in dict.fromkeys(public_files):
    if path.exists() and OLD_BASE in path.read_text(encoding="utf-8"):
        errors.append(f"retired production domain remains in public output: {path.relative_to(ROOT)}")

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
    if "googletagmanager.com/gtag/js" in text or "gtag('config','G-MR6ZXXL5JQ')" in text:
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
        if not profile.exists():
            errors.append(f"missing global organization profile: {iso}/{item['id']}")
            continue
        profile_text=profile.read_text(encoding="utf-8")
        for token in ("Kapcsolati háló","Programforrások","Közösségi oldalak és nyilvános csatornák","Adatgazda és ellenőrzés",'name="author"','rel="alternate"'):
            if token not in profile_text:
                errors.append(f"rich organization profile layer missing ({token}): {iso}/{item['id']}")
        blocks=re.findall(r'<script type="application/ld\+json">(.*?)</script>',profile_text,re.S)
        try:
            payload=json.loads(blocks[0].replace("<\\/","</"))
            graph=payload.get("@graph",[])
            page=next(x for x in graph if x.get("@type")=="ProfilePage")
            entity=next(x for x in graph if x.get("@type")=="Organization" and x.get("@id")==f"{BASE}/countries/{iso}/organizations/{item['id']}.html#entity")
            if not page.get("publisher") or not page.get("dateModified") or page.get("inLanguage")!="hu":
                errors.append(f"profile E-E-A-T schema incomplete: {iso}/{item['id']}")
            if not entity.get("areaServed") or not entity.get("mainEntityOfPage"):
                errors.append(f"organization entity schema incomplete: {iso}/{item['id']}")
        except Exception as ex:
            errors.append(f"invalid global organization profile schema: {iso}/{item['id']} -> {ex}")

for country in globaldb.get("countries",[]):
    iso=country["iso2"]
    edu_path=ROOT/"data"/"countries"/iso/"education.json"
    if not edu_path.exists(): continue
    edoc=json.loads(edu_path.read_text(encoding="utf-8"))
    for item in edoc.get("institutions",edoc.get("education",edoc.get("items",[]))):
        if not item.get("id"): continue
        profile=ROOT/"countries"/iso/"education"/f"{item['id']}.html"
        if not profile.exists():
            errors.append(f"missing global education profile: {iso}/{item['id']}")
            continue
        profile_text=profile.read_text(encoding="utf-8")
        for token in ("Források és ellenőrzés",'name="author"','rel="alternate"',"ui.js"):
            if token not in profile_text:
                errors.append(f"rich education profile layer missing ({token}): {iso}/{item['id']}")
        blocks=re.findall(r'<script type="application/ld\+json">(.*?)</script>',profile_text,re.S)
        try:
            payload=json.loads(blocks[0].replace("<\\/","</"))
            graph=payload.get("@graph",[])
            page=next(x for x in graph if x.get("@type")=="ProfilePage")
            entity=next(x for x in graph if x.get("@type")=="EducationalOrganization")
            if not page.get("publisher") or not page.get("dateModified") or page.get("inLanguage")!="hu":
                errors.append(f"education profile E-E-A-T schema incomplete: {iso}/{item['id']}")
            if not entity.get("areaServed") or not entity.get("mainEntityOfPage"):
                errors.append(f"education entity schema incomplete: {iso}/{item['id']}")
        except Exception as ex:
            errors.append(f"invalid global education profile schema: {iso}/{item['id']} -> {ex}")

for p in ("llms.txt","ai.txt","ai-entry.json","entity.jsonld","robots.txt","sitemap.xml","forrasok.html","adatminoseg.html","ui.js","world.js","country.js","data/global-search-index.json","data/global-events.json","data/human-language-audit.json","data/ecosystem-quality-audit.json","docs/content-ui-policy.md"):
    if not (ROOT/p).exists(): errors.append(f"missing trust/search artifact: {p}")

registry_country_ids={c.get("iso2") for c in globaldb.get("countries",[]) if c.get("iso2")}
search_country_ids={x.get("country") for x in global_search.get("items",[]) if x.get("type")=="country"}
if search_country_ids != registry_country_ids:
    errors.append(f"global search country coverage mismatch: {len(search_country_ids)} != {len(registry_country_ids)}")

expected_directory=[]
for country in globaldb.get("countries",[]):
    if country.get("researchStatus") not in {"reviewed","verified-zero"}: continue
    iso=country.get("iso2")
    base=ROOT/"data"/"countries"/iso
    odoc=json.loads((base/"organizations.json").read_text(encoding="utf-8")) if (base/"organizations.json").exists() else {}
    edoc=json.loads((base/"education.json").read_text(encoding="utf-8")) if (base/"education.json").exists() else {}
    expected_directory.extend((iso,x.get("id")) for x in odoc.get("organizations",odoc.get("items",[])) if x.get("id") and x.get("entityClass")!="activity")
    expected_directory.extend((iso,x.get("id")) for x in edoc.get("institutions",edoc.get("education",edoc.get("items",[]))) if x.get("id"))
directory_items=[x for x in global_search.get("items",[]) if x.get("type")=="organization"]
actual_directory={(x.get("country"),x.get("id")) for x in directory_items}
if actual_directory != set(expected_directory):
    errors.append(f"homepage organization directory coverage mismatch: {len(actual_directory)} != {len(expected_directory)}")
for item in directory_items:
    if not item.get("entityType") or not item.get("category") or not item.get("href") or "summary" not in item:
        errors.append(f"homepage organization search item incomplete: {item.get('country')}/{item.get('id')}")

quality_text=(ROOT/"adatminoseg.html").read_text(encoding="utf-8")
for token in ('href="./#vilag"','href="./#szervezetek"','href="./countries/at/#oktatas"','href="./#programnaptar"'):
    if token not in quality_text:
        errors.append(f"data-quality navigation target missing: {token}")
quality_expectations=(
    (f'<strong>{len(org.get("organizations",[]))}</strong> nyilvántartott közösség és intézmény', "organization count"),
    (f'<strong>{len(edu.get("institutions",[]))}</strong> oktatási lehetőség', "education count"),
    (f'<strong>{len(ev.get("events",[]))}</strong> forrással rendelkező program', "event count"),
    (f'Szervezeti adat frissítve: {org.get("updated")}', "organization timestamp"),
    (f'Oktatási adat frissítve: {edu.get("updated")}', "education timestamp"),
    (f'Eseményadat frissítve: {ev.get("updated")}', "event timestamp"),
)
for token,label in quality_expectations:
    if token not in quality_text:
        errors.append(f"stale data-quality page: {label} does not match canonical data")

ai_entry=json.loads((ROOT/"ai-entry.json").read_text(encoding="utf-8"))
for key,expected in (
    ("organizations",len(org.get("organizations",[]))),
    ("education",len(edu.get("institutions",[]))),
    ("events",len(ev.get("events",[]))),
):
    if ai_entry.get("counts",{}).get(key)!=expected:
        errors.append(f"stale ai-entry count: {key}")

taxonomy_audit=json.loads((ROOT/"data/taxonomy-audit.json").read_text(encoding="utf-8"))
for key,expected in (
    ("organizations",len(org.get("organizations",[]))),
    ("education",len(edu.get("institutions",[]))),
    ("events",len(ev.get("events",[]))),
):
    if taxonomy_audit.get("summary",{}).get(key)!=expected:
        errors.append(f"stale taxonomy-audit count: {key}")

for p in ("index.html","forrasok.html","szervezet.html"):
    text=(ROOT/p).read_text(encoding="utf-8")
    if "googletagmanager.com/gtag/js" in text or "gtag('config','G-MR6ZXXL5JQ')" in text:
        errors.append(f"non-consent analytics bootstrap present: {p}")
    if "ui.js" not in text:
        errors.append(f"shared consent/navigation controller missing: {p}")

home=(ROOT/"index.html").read_text(encoding="utf-8")
for token in ('id="szervezetek"','id="organizationCountry"','id="organizationType"','id="organizationSearch"','rel="alternate"','SearchAction'):
    if token not in home: errors.append(f"homepage organization/SEO layer missing: {token}")
world_js = (ROOT / "world.js").read_text(encoding="utf-8")
if '"#szervezetek":"countries/at/' in world_js:
    errors.append("homepage organization anchor is shadowed by legacy Austria redirect")
for token in ('addEventListener("load", decorateMap)', 'contentDocument?.readyState === "complete"', "decorateMap();"):
    if token not in world_js: errors.append(f"world map cached-SVG paint regression: missing {token}")
for token in ("bindEmbeddedPan", "pointerdown", "pointermove", "data-map-fullscreen"):
    if token not in world_js: errors.append(f"world map pan/fullscreen regression: missing {token}")

ui_js = (ROOT / "ui.js").read_text(encoding="utf-8")
if "G-1FC22JEX2F" in ui_js:
    errors.append("retired GA4 measurement id remains in ui.js")
for token in ("G-MR6ZXXL5JQ", 'gtag("consent","default"', 'gtag("consent","update"', "clearAnalyticsCookies"):
    if token not in ui_js: errors.append(f"consent-first Analytics regression: missing {token}")

styles=(ROOT/"styles.css").read_text(encoding="utf-8")
for token in ("grid-auto-rows:1fr","-webkit-line-clamp:2","text-overflow:ellipsis","overflow-wrap:anywhere","map-fullscreen-fallback","72vh"):
    if token not in styles: errors.append(f"equal-cell/overflow policy missing from CSS: {token}")

human_audit=json.loads((ROOT/"data/human-language-audit.json").read_text(encoding="utf-8"))
if human_audit.get("findings"):
    errors.append(f"human-language audit still has {len(human_audit['findings'])} finding(s)")
ecosystem_audit=json.loads((ROOT/"data/ecosystem-quality-audit.json").read_text(encoding="utf-8"))
if ecosystem_audit.get("blockingIssues"):
    errors.append(f"ecosystem-quality audit still has {len(ecosystem_audit['blockingIssues'])} blocking issue(s)")

country_js = (ROOT / "country.js").read_text(encoding="utf-8")
for token in ("pointerdown", "pointermove", "pointerup", "pointercancel", "setPointerCapture", "scale", "translate3d", "data-country-map-reset", "data-map-fullscreen", "clamp", 'obj.contentDocument?.readyState==="complete"', "dorappCountryMapBound"):
    if token not in country_js: errors.append(f"country map pan/zoom regression: missing {token}")
map_generator = (ROOT / "scripts" / "generate_country_region_maps.py").read_text(encoding="utf-8")
for token in ('VERSION="5.1.2"', "longitude_wrap_start", "wrap_longitude", "offset_x=(width-content_width)/2", "offset_y=(height-content_height)/2"):
    if token not in map_generator: errors.append(f"country map projection regression: missing {token}")
for iso in ("at", "nl", "be", "us"):
    page = (ROOT / "countries" / iso / "index.html").read_text(encoding="utf-8")
    if 'country-map-viewport' not in page or 'data-country-map-zoom-in' not in page: errors.append(f"{iso}: shared country map controller markup missing")
    if 'id="kereso"' in page and page.index('id="kereso"') > page.index('id="terkep"'): errors.append(f"{iso}: search must remain above map")

print(f"static_output organizations={len(org.get('organizations',[]))} education={len(edu.get('institutions',[]))} events={len(ev.get('events',[]))}")
if errors:
    print("\n".join("ERROR: "+x for x in errors))
    sys.exit(1)
