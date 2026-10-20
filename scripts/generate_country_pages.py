#!/usr/bin/env python3
import json, html, unicodedata
from datetime import datetime
from pathlib import Path
import pycountry

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BASE = "https://www.diaszporaterkep.hu"
INDEXABLE = {"reviewed", "verified-zero"}
COUNTRY_ASSET_VERSION = "20261020-event-card-2"

def read(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def esc(value):
    return html.escape(str(value or ""), quote=True)

def normalized(value):
    text=unicodedata.normalize("NFKD",str(value or "")).encode("ascii","ignore").decode("ascii").lower()
    return " ".join(text.replace("_"," ").replace("-"," ").split())

def human_type(value):
    raw=str(value or "").strip()
    key=normalized(raw)
    rules=(
        (("egyhaz","church","parish","mission"),"Egyház"),
        (("cserkesz","scout"),"Cserkészet"),
        (("media","radio","newspaper","magazine"),"Média"),
        (("neptanc","folk dance","hagyomany"),"Hagyományőrzés"),
        (("iskola","school","education","ovoda","kindergarten","bolcsode","university"),"Oktatás"),
        (("kultura","cultural","theatre","szinhaz","music","zene","choir","enekkar"),"Kultúra"),
        (("business","professional","kamara","gazdasag"),"Szakmai / gazdasági"),
    )
    for needles,label in rules:
        if any(needle in key for needle in needles): return label
    return "Közösség" if raw else "Szervezet"

def country_data(iso):
    base = DATA / "countries" / iso
    org_data = read(base / "organizations.json", {"organizations":[]})
    edu_data = read(base / "education.json", {"institutions":[]})
    event_data = read(base / "events.json", {"events":[]})
    orgs = org_data.get("organizations", org_data.get("items", []))
    edus = edu_data.get("institutions", edu_data.get("education", edu_data.get("items", [])))
    events = event_data.get("events", event_data.get("items", []))
    divisions = org_data.get("states") or org_data.get("regions") or []
    if not divisions:
        try:
            if iso.lower()=="es":
                divisions = [
                    {"id":"andalucia","name":"Andalúzia","mapRegions":["Almería","Cádiz","Córdoba","Granada","Huelva","Jaén","Málaga","Sevilla"],"mapLabel":"Sevilla"},
                    {"id":"aragon","name":"Aragónia","mapRegions":["Huesca","Teruel","Zaragoza"],"mapLabel":"Zaragoza"},
                    {"id":"asturias","name":"Asztúria","mapRegions":["Asturias"],"mapLabel":"Asturias"},
                    {"id":"baleares","name":"Baleár-szigetek","mapRegions":["Baleares"],"mapLabel":"Baleares"},
                    {"id":"canarias","name":"Kanári-szigetek","mapRegions":["Las Palmas","Santa Cruz de Tenerife"],"mapLabel":"Santa Cruz de Tenerife"},
                    {"id":"cantabria","name":"Kantábria","mapRegions":["Cantabria"],"mapLabel":"Cantabria"},
                    {"id":"castilla-la-mancha","name":"Kasztília–La Mancha","mapRegions":["Albacete","Ciudad Real","Cuenca","Guadalajara","Toledo"],"mapLabel":"Toledo"},
                    {"id":"castilla-y-leon","name":"Kasztília és León","mapRegions":["Ávila","Burgos","León","Palencia","Salamanca","Segovia","Soria","Valladolid","Zamora"],"mapLabel":"Valladolid"},
                    {"id":"cataluna","name":"Katalónia","mapRegions":["Barcelona","Gerona","Lérida","Tarragona"],"mapLabel":"Barcelona"},
                    {"id":"ceuta","name":"Ceuta","mapRegions":["Ceuta"],"mapLabel":"Ceuta"},
                    {"id":"extremadura","name":"Extremadura","mapRegions":["Badajoz","Cáceres"],"mapLabel":"Badajoz"},
                    {"id":"galicia","name":"Galícia","mapRegions":["La Coruña","Lugo","Orense","Pontevedra"],"mapLabel":"La Coruña"},
                    {"id":"madrid","name":"Madrid","mapRegions":["Madrid"],"mapLabel":"Madrid"},
                    {"id":"melilla","name":"Melilla","mapRegions":["Melilla"],"mapLabel":"Melilla"},
                    {"id":"murcia","name":"Murcia","mapRegions":["Murcia"],"mapLabel":"Murcia"},
                    {"id":"navarra","name":"Navarra","mapRegions":["Navarra"],"mapLabel":"Navarra"},
                    {"id":"pais-vasco","name":"Baszkföld","mapRegions":["Álava","Bizkaia","Gipuzkoa"],"mapLabel":"Bizkaia"},
                    {"id":"rioja","name":"La Rioja","mapRegions":["La Rioja"],"mapLabel":"La Rioja"},
                    {"id":"valencia","name":"Valenciai Közösség","mapRegions":["Alicante","Castellón","Valencia"],"mapLabel":"Valencia"},
                ]
            else:
                divisions = [{"id": s.name, "name": s.name, "code": s.code} for s in sorted(pycountry.subdivisions.get(country_code=iso.upper()), key=lambda x: x.name)]
        except Exception:
            divisions = []
    names = {str(x.get("id")): str(x.get("name") or x.get("label") or x.get("id")) for x in divisions if x.get("id")}
    return org_data, orgs, edus, events, divisions, names

def region_key(item):
    return str(item.get("region") or item.get("state") or ("Országos" if item.get("scope") == "national" else "") or "Régió nélkül")

def region_label(key, names):
    return names.get(key, key)

def counts_by_region(orgs):
    out={}
    for o in orgs:
        if o.get("entityClass") == "activity":
            continue
        key=region_key(o)
        if key and key!="Régió nélkül":
            out[key]=out.get(key,0)+1
    return out

def region_inventory(divisions, orgs, edus, events, names):
    ordered=[]
    seen=set()
    for d in divisions:
        key=str(d.get("id") or "")
        if key and key not in seen:
            label=str(d.get("name") or d.get("label") or key)
            map_name=str(d.get("mapName") or d.get("de") or d.get("en") or label)
            ordered.append((key, label, map_name, d.get("mapRegions") or [map_name], d.get("mapLabel") or map_name))
            seen.add(key)
    discovered=set()
    for x in [*orgs,*edus,*events]:
        key=region_key(x)
        if key and key not in {"Régió nélkül","Országos"} and key not in seen:
            discovered.add(key)
    for key in sorted(discovered, key=lambda x: region_label(x,names).casefold()):
        label=region_label(key,names)
        ordered.append((key,label,label,[label],label))
        seen.add(key)
    return ordered

def map_html(iso, regions, counts):
    if not regions:
        return '<div class="country-map-shell"><div class="country-map-board"><div class="empty">Ehhez az országhoz / területhez nincs külön első szintű közigazgatási felosztás rögzítve.</div></div><div class="country-map-legend"><span>Önálló admin-1 egység nélkül.</span></div></div>'
    buttons="".join(
        f'<button class="country-region-button" type="button" data-region="{esc(key)}" data-map-region="{esc(map_name)}" data-map-regions="{esc("|".join(map_regions))}" data-map-label="{esc(map_label)}"><span>{esc(label)}</span><b class="map-count">{counts.get(key,0)}</b></button>'
        for key,label,map_name,map_regions,map_label in regions
    )
    svg=ROOT/"assets"/"maps"/f"{iso}.svg"
    actual=(f'<div class="country-map-interactive"><div class="country-map-toolbar" aria-label="Térkép nagyítása"><button type="button" data-country-map-zoom-out aria-label="Kicsinyítés">−</button><button type="button" data-country-map-zoom-in aria-label="Nagyítás">+</button><button type="button" data-country-map-reset aria-label="Térkép alaphelyzet">↺</button><span data-country-map-status aria-live="polite">100%</span></div><div class="country-map-viewport"><object id="countrySubdivisionMap" class="country-subdivision-map" data="../../assets/maps/{esc(iso)}.svg" type="image/svg+xml" aria-label="{esc(iso.upper())} tartományi térképe"></object></div></div>' if svg.exists() else '')
    return (
        '<div class="country-map-shell">'
        + actual +
        f'<div class="country-map-board country-map-{esc(iso)}" aria-label="Tartományok / első szintű közigazgatási egységek">{buttons}</div>'
        '<div class="country-map-legend"><span><i></i> A szám az ellenőrzött civil és hivatalos magyar szervezetek együttes darabszáma.</span><span>Határgeometria: Natural Earth Admin 1.</span></div>'
        '</div>'
    )

def country_research_html(org_data):
    leads=org_data.get("researchLeads") or []
    sources=org_data.get("discoverySources") or []
    coverage=org_data.get("researchCoverage") or []
    if not (leads or sources or coverage or org_data.get("researchMethodology")):
        return ""
    lead_html="".join(
        f'<article class="card research-lead"><div class="meta">{esc(x.get("city") or x.get("region") or "országos")} · További ellenőrzés szükséges</div><h3>{esc(x.get("name"))}</h3><p>{esc(x.get("reason"))}</p><div class="links">{(f"<a href=\"{esc(x.get('url'))}\" target=\"_blank\" rel=\"noopener external\">Közösségi hivatkozás ↗</a>" if x.get("url") else "")}<a href="{esc(x.get("sourceUrl"))}" target="_blank" rel="noopener external">Ellenőrzési forrás ↗</a></div></article>'
        for x in leads
    )
    source_html="".join(
        f'<li><a href="{esc(x.get("url"))}" target="_blank" rel="noopener external">{esc(x.get("label") or x.get("url"))} ↗</a>{(f" — {esc(x.get('scope'))}" if x.get("scope") else "")}</li>'
        for x in sources if x.get("url")
    )
    coverage_html="".join(
        f'<li><strong>{esc(x.get("name") or x.get("region"))}:</strong> {esc(x.get("status"))}</li>'
        for x in coverage
    )
    return (
        '<section id="forrasok" class="section"><div class="wrap">'
        '<div class="section-head"><div><div class="eyebrow">Átláthatóság</div><h2>Források és kutatási állapot</h2>'
        f'<p>{esc(org_data.get("researchMethodology") or "Forrásjegyzék és az ellenőrzés állapota.")}</p></div></div>'
        '<div class="trust-grid"><div><h3>Területi lefedettség</h3><ul class="source-list">'+coverage_html+'</ul></div>'
        '<div><h3>Kutatási források</h3><ul class="source-list">'+source_html+'</ul></div></div>'
        +('<h3 class="research-leads-title">Ellenőrzésre váró közösségi nyomok</h3><div class="cards research-leads">'+lead_html+'</div>' if lead_html else '')
        +'</div></section>'
    )

def org_cards(orgs, names):
    rows=[o for o in orgs if o.get("entityClass")!="activity" and o.get("id") and o.get("name")]
    if not rows:
        return '<div id="countryOrgGrid" class="cards"></div><div id="countryOrgEmpty" class="empty">Jelenleg nincs publikálható, ellenőrzött szervezeti rekord.</div>'
    def one(o):
        socials=[]
        for label,key in (("Weboldal","website"),("Facebook","facebook"),("Instagram","instagram"),("YouTube","youtube"),("LinkedIn","linkedin")):
            if o.get(key): socials.append(f'<a href="{esc(o.get(key))}" target="_blank" rel="noopener external">{label} ↗</a>')
        for ch in o.get("publicChannels") or []:
            if ch.get("url"):
                socials.append(f'<a href="{esc(ch.get("url"))}" target="_blank" rel="noopener external">{esc(ch.get("label") or ch.get("platform") or "Közösségi oldal")} ↗</a>')
        calendars=[x for x in (o.get("calendarSources") or []) if x.get("url")]
        auto=sum(1 for x in calendars if x.get("ingestEvents"))
        calendar_note=""
        if calendars:
            calendar_note=f'<p class="site-status"><strong>Programforrás:</strong> {len(calendars)} ellenőrzött forrás' + (f' · {auto} automatikus' if auto else '') + '</p>'
        return (
            f'<article class="card country-org-card" data-org-id="{esc(o.get("id"))}" data-region="{esc(region_key(o))}">'
            f'<div class="meta" title="{esc(o.get("type") or "szervezet")}">{esc(region_label(region_key(o),names))} · {esc(o.get("city") or "országos")} · {esc(human_type(o.get("type")))}</div>'
            f'<h3>{esc(o.get("name"))}</h3>'
            f'<p>{esc(o.get("summary") or o.get("intro") or "Ellenőrzött magyar diaszpóra-szervezet.")}</p>'
            f'{calendar_note}<div class="links"><a href="organizations/{esc(o.get("id"))}.html">Teljes adatlap →</a>{"".join(socials[:3])}</div>'
            '</article>'
        )
    return '<div id="countryOrgGrid" class="cards">'+"".join(one(o) for o in sorted(rows,key=lambda x:str(x.get("name","")).casefold()))+'</div><div id="countryOrgEmpty" class="empty" hidden>Nincs a szűrésnek megfelelő szervezet.</div>'

def edu_cards(edus, names):
    rows=[e for e in edus if e.get("id") and e.get("name")]
    return '<div id="countryEducationGrid" class="cards">'+"".join(
        f'<article class="card" data-region="{esc(region_key(e))}"><div class="meta" title="{esc(e.get("type") or "oktatás")}">{esc(region_label(region_key(e),names))} · {esc(e.get("city") or "")} · Oktatás</div><h3>{esc(e.get("name"))}</h3><p>{esc(e.get("summary") or e.get("intro") or "Magyar oktatási lehetőség.")}</p><div class="links"><a href="education/{esc(e.get("id"))}.html">Teljes adatlap →</a>{(f"""<a href="{esc(e.get("website"))}" target="_blank" rel="noopener external">Weboldal ↗</a>""" if e.get("website") else "")}</div></article>'
        for e in sorted(rows,key=lambda x:str(x.get("name","")).casefold())
    )+'</div><div id="countryEducationEmpty" class="empty" hidden>Nincs a szűrésnek megfelelő oktatási rekord.</div>'

def event_cards(events, names):
    rows=[e for e in events if e.get("id") and (e.get("name") or e.get("title"))]
    definitions={x.get("id"):x.get("label") for x in (read(DATA/"events.json",{}).get("programCategoryDefinitions") or []) if x.get("id")}
    def one(e):
        title=e.get("name") or e.get("title") or ""
        detail=f'events/{esc(e.get("id"))}.html'
        categories=e.get("programCategories") or e.get("categories") or []
        if isinstance(categories,str): categories=[categories]
        labels=[definitions.get(str(value),str(value).replace("_"," ").replace("-"," ")) for value in categories]
        if not labels and categories:
            labels=[str(value).replace("_"," ").replace("-"," ") for value in categories]
        category=" · ".join(labels) or "Magyar közösségi program"
        start=e.get("startDate") or e.get("date")
        display_date=str(start or "")
        if start:
            try:
                parsed=datetime.fromisoformat(str(start).replace("Z","+00:00"))
                display_date=f"{parsed.year}. {parsed.month:02d}. {parsed.day:02d}." + (f" {parsed.hour:02d}:{parsed.minute:02d}" if "T" in str(start) else "")
            except (TypeError,ValueError):
                pass
        date_text=f'<time class="event-card-date" datetime="{esc(start)}">{esc(display_date)}</time>' if start else ""
        location=" · ".join(str(value) for value in (e.get("venue"),e.get("city")) if value)
        organizer=e.get("organizer")
        description=e.get("description") or e.get("summary")
        description_html=f'<p class="event-card-description">{esc(description)}</p>' if description else ""
        meta_parts=[]
        if location: meta_parts.append(f'<span><strong>Helyszín:</strong> {esc(location)}</span>')
        if organizer: meta_parts.append(f'<span><strong>Szervező:</strong> {esc(organizer)}</span>')
        meta=f'<p class="event-card-meta">{"".join(meta_parts)}</p>' if meta_parts else ""
        source=e.get("sourceUrl")
        source_link=(f'<a class="event-card-source" href="{esc(source)}" target="_blank" rel="noopener external" aria-label="Eredeti forrás: {esc(title)}">Eredeti forrás ↗</a>' if source else "")
        return (f'<article class="event event-directory-card" data-region="{esc(region_key(e))}">'
                f'<a class="event-card-main" href="{detail}" aria-label="{esc(title)} – program adatlap">'
                f'<span class="event-card-category">{esc(category)}</span><h3>{esc(title)}</h3>{date_text}'
                f'{meta}{description_html}'
                '<span class="event-card-action">Program adatlap →</span></a>'
                f'{source_link}</article>')
    return '<div id="countryEventGrid" class="event-grid">'+"".join(
        one(e) for e in sorted(rows,key=lambda x:str(x.get("startDate") or x.get("date") or ""))
    )+'</div><div id="countryEventEmpty" class="empty" hidden>Nincs a szűrésnek megfelelő közelgő program.</div>'

def search_html(name):
    return f'''<section id="kereso" class="section directory-search"><div class="wrap">
      <div class="section-head"><div><div class="eyebrow">Országos kereső</div><h2>Közösségek és programok</h2><p>Keress {esc(name)} magyar szervezetei, városai, tevékenységei, programjai és helyszínei között.</p></div></div>
      <div class="directory-search-grid country-directory-search-grid">
        <label>Tartomány / régió<select id="countryRegion"><option value="">Minden tartomány / régió</option></select></label>
        <label>Város<select id="countryCity"><option value="">Minden város</option></select></label>
        <label>Szervezet<select id="countryOrganization"><option value="">Minden szervezet</option></select></label>
        <label>Tevékenység<select id="countryActivity"><option value="">Minden tevékenység</option></select></label>
        <label>Program<select id="countryProgram"><option value="">Minden program</option></select></label>
        <label>Kapcsolat<input id="countryContact" type="search" autocomplete="off" placeholder="Név, e-mail vagy telefon"></label>
        <label>Cím / helyszín<input id="countryAddress" type="search" autocomplete="off" placeholder="Utca, helyszín vagy cím"></label>
        <label class="directory-query">Szabad keresés<input id="countryQuery" type="search" autocomplete="off" placeholder="Szervezet, közösség, tevékenység, program…"></label>
        <button id="countryReset" class="directory-reset" type="button">Szűrők törlése</button>
      </div>
      <div id="countryDirectoryCount" class="result-count" aria-live="polite"></div>
      <div id="countryDirectoryResults" class="directory-results"></div>
    </div></section>'''

registry=read(DATA/"global.json",{"countries":[]})
for country in registry.get("countries",[]):
    iso=country["iso2"]
    out=ROOT/"countries"/iso
    out.mkdir(parents=True,exist_ok=True)
    names=country.get("name",{})
    name=names.get("hu") or names.get("en") or iso.upper()
    status=country.get("researchStatus","unresearched")
    counts=country.get("counts",{})
    org_doc,orgs,edus,events,divisions,division_names=country_data(iso)
    has_data=bool(orgs or edus or events)
    regions=region_inventory(divisions,orgs,edus,events,division_names)
    region_counts=counts_by_region(orgs)
    indexable=status in INDEXABLE
    robots="index,follow" if indexable else "noindex,follow"

    if True:  # All registry countries receive a consistent country directory.
        status_banner="" if indexable else '<div class="country-status-banner"><strong>Az ország adatbázisa még épül.</strong> Az itt látható rekordok ellenőrzöttek, de a területi lefedettség még nem teljes.</div>'
        body_sections=(
            status_banner+
            search_html(name)+
            f'<section id="terkep" class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Területi térkép</div><h2>Hol keresel?</h2><p>Válassz tartományt / első szintű régiót. A szám mutatja, hány ellenőrzött magyar szervezetet tartunk nyilván ott.</p></div><button id="countryAllRegions" class="text-btn" type="button">Egész ország</button></div>{map_html(iso,regions,region_counts)}<div id="countryMapSummary" class="state-summary" aria-live="polite"></div></div></section>'+
            f'<section id="kozossegek" class="section muted"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Közösségek</div><h2>Szervezetek és közösségek</h2><p>Ellenőrzött bemutatkozások, közvetlen szervezeti adatlapok és hivatalos elérhetőségek.</p></div></div><div id="countryOrgCount" class="result-count"></div>{org_cards(orgs,division_names)}</div></section>'+ 
            f'<section id="oktatas" class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Magyar oktatás</div><h2>Oktatási lehetőségek</h2><p>Magyar iskolák, óvodák, hétvégi és online oktatási lehetőségek ellenőrzött forrásokból.</p></div></div><div id="countryEducationCount" class="result-count"></div>{edu_cards(edus,division_names)}</div></section>'+ 
            f'<section id="programok" class="section muted"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Programnaptár</div><h2>Közelgő programok</h2><p>Csak ellenőrzött dátummal, magyar vonatkozással és forráshivatkozással rendelkező program jelenik meg.</p></div></div><div id="countryEventCount" class="result-count"></div>{event_cards(events,division_names)}</div></section>'+
            country_research_html(org_doc)
        )
    else:
        body_sections=(
            '<div class="country-status-banner"><strong>Az ország kutatása még nem jutott el publikálható szervezeti rekordig.</strong> A térkép első szintű közigazgatási egységei már böngészhetők, a szervezetszám ezért jelenleg 0 lehet.</div>'+
            f'<section id="terkep" class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Területi térkép</div><h2>Első szintű közigazgatási egységek.</h2><p>A kutatás előkészített területi váza. A szervezetszám csak ellenőrzött rekordból nőhet.</p></div></div>{map_html(iso,regions,region_counts)}<div id="countryMapSummary" class="state-summary">{sum(region_counts.values())} ellenőrzött szervezet.</div><p><a class="btn" href="../../">Vissza a világtérképhez</a></p></div></section>'
        )

    title_name=name if iso!="es" or names.get("hu") else "Spanyolország"
    title=f"Magyar közösségek – {title_name} | DORAPP"
    canonical=f"{BASE}/countries/{iso}/"
    description=f"{title_name} magyar szervezeteinek, közösségeinek, oktatásának és programjainak forrásalapú DORAPP országoldala."
    modified=country.get("lastBroadVerifiedAt") or country.get("lastResearchAttemptAt")
    nav_links='<a href="../../">Világ</a><a href="#terkep">Térkép</a><a href="#kereso">Kereső</a><a href="#kozossegek">Szervezetek</a><a href="#programok">Programok</a>'
    item_urls=[f"{canonical}organizations/{o.get('id')}.html" for o in orgs if o.get("id") and o.get("entityClass")!="activity"]
    schema={"@context":"https://schema.org","@type":"CollectionPage","@id":canonical+"#page","name":title,"description":description,"url":canonical,"inLanguage":"hu","dateModified":modified,"isPartOf":{"@id":BASE+"/#website"},"publisher":{"@type":"Organization","@id":BASE+"/#organization","name":"Központi Szövetség","url":"https://www.kozpontiszovetseg.at/"},"about":{"@type":"Country","name":names.get("en") or name},"mainEntity":{"@type":"ItemList","numberOfItems":len(item_urls),"itemListElement":[{"@type":"ListItem","position":i+1,"url":u} for i,u in enumerate(item_urls)]}}
    country_css_version=COUNTRY_ASSET_VERSION
    doc=f'''<!doctype html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><link rel="icon" href="../../favicon.svg" type="image/svg+xml"><title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="author" content="Központi Szövetség"><meta name="robots" content="{robots}"><link rel="canonical" href="{canonical}"><link rel="alternate" type="text/plain" href="../../llms.txt" title="LLM információ"><meta property="og:type" content="website"><meta property="og:site_name" content="DORAPP"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{canonical}"><meta name="twitter:card" content="summary"><link rel="stylesheet" href="../../styles.css?v={country_css_version}"><link rel="stylesheet" href="/design-editorial.css?v=20261015-2"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False)}</script></head><body data-country="{esc(iso)}"><a class="skip" href="#content">Ugrás a tartalomhoz</a><header class="topbar"><div class="wrap navrow"><a class="brand" href="../../"><span class="mark">HU</span><span>DORAPP</span></a><nav>{nav_links}</nav></div></header><main id="content"><section class="hero country-hero"><div class="wrap"><div class="eyebrow">DORAPP · {iso.upper()}</div><h1>{esc(name)} <span>magyar közösségei</span></h1><p class="lead">{counts.get("organizations",0)} ellenőrzött szervezet · {counts.get("education",0)} oktatási rekord · {counts.get("events",0)} program a jelenlegi adatállapot szerint.</p><p class="hero-proof"><strong>Forrásalapú rendszer.</strong> Kutatási állapot: {esc(status)}.</p></div></section>{body_sections}</main><footer><div class="wrap footer-grid"><div><b>DORAPP</b><p>Forrásalapú magyar diaszpóra-címtár és programnaptár.</p></div><div><a href="../../forrasok.html">Források és módszertan</a><br><a href="../../adatminoseg.html">Adatminőség</a></div><div><a href="https://www.kozpontiszovetseg.at/kapcsolat" target="_blank" rel="noopener external">Impresszum / kapcsolat ↗</a></div><div class="site-credit">A <a href="https://www.magyariskola.at/" target="_blank" rel="noopener external">Bécsi Magyar Iskola</a> – <a href="https://rolunk.at/aktualis/a-fiataloknak-ma-mar-bizonyitek-kell-egy-becsi-kreativ-kozosseg-uj-generaciot-epit/" target="_blank" rel="noopener external">Be Smart Kids Club</a> csapata hozta létre.<br><a href="mailto:marketing@kozpontiszovetseg.at">marketing@kozpontiszovetseg.at</a></div></div></footer><script src="../../country.js?v={country_css_version}" defer></script><script src="../../ui.js?v=20261015-trust-contact-1" defer></script></body></html>'''
    (out/"index.html").write_text(doc,encoding="utf-8")

print(f"Generated {len(registry.get('countries',[]))} country routes")
