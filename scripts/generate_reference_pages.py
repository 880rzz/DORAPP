#!/usr/bin/env python3
import json, html
from pathlib import Path
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
BASE="https://diaszpora.kozpontiszovetseg.at"
ORG=json.loads((ROOT/"data/organizations.json").read_text(encoding="utf-8"))
EDU=json.loads((ROOT/"data/education.json").read_text(encoding="utf-8"))
EV=json.loads((ROOT/"data/events.json").read_text(encoding="utf-8"))
SOURCE_HEALTH=json.loads((ROOT/"data/source-health.json").read_text(encoding="utf-8")) if (ROOT/"data/source-health.json").exists() else {"sources":[]}
EDU_HEALTH=json.loads((ROOT/"data/education-site-health.json").read_text(encoding="utf-8")) if (ROOT/"data/education-site-health.json").exists() else {"sites":[]}

ORG_DIR=ROOT/"szervezetek"
EVENT_DIR=ROOT/"esemenyek"
STATE_DIR=ROOT/"tartomanyok"
CATEGORY_DIR=ROOT/"kategoriak"
for d in (EVENT_DIR,STATE_DIR,CATEGORY_DIR): d.mkdir(exist_ok=True)

states={x["id"]:x for x in ORG.get("states",[])}
orgs=ORG.get("organizations",[])
org_by_id={x["id"]:x for x in orgs}
education=EDU.get("institutions",[])
events=EV.get("events",[])
categories=ORG.get("categoryDefinitions",[])
DATA_MODIFIED=max(str(x or "")[:10] for x in (ORG.get("updated"),EDU.get("updated"),EV.get("updated")) if x)

PUBLISHER={
  "@type":"Organization",
  "@id":BASE+"/#publisher",
  "name":"Ausztriai Magyar Egyesületek és Szervezetek Központi Szövetsége",
  "url":"https://www.kozpontiszovetseg.at/",
  "identifier":{"@type":"PropertyValue","propertyID":"ZVR","value":"079797621"}
}

def esc(v): return html.escape(str(v or ""),quote=True)
def jsonld(data): return json.dumps(data,ensure_ascii=False,separators=(",",":")).replace("</","<\\/")
def footer(prefix="../"):
    return f'''<footer><div class="wrap footer-grid">
    <div><b>Magyar Programok Ausztriában</b><p>Forrásalapú címtár, oktatási adatbázis és programnaptár egész Ausztriából.</p></div>
    <div><a href="{prefix}forrasok.html">Módszertan és források</a><br><a href="https://www.kozpontiszovetseg.at/kapcsolat" target="_blank" rel="noopener external">Impresszum / kapcsolat ↗</a><br><a href="https://www.kozpontiszovetseg.at/post/gdpr-ai-trust" target="_blank" rel="noopener external">GDPR & AI Trust ↗</a></div>
    <div>Fejlesztette a <a href="https://rolunk.at/aktualis/a-fiataloknak-ma-mar-bizonyitek-kell-egy-becsi-kreativ-kozosseg-uj-generaciot-epit/" target="_blank" rel="noopener external">Be Smart Kids Club csapata</a><br><a href="https://business.vipach.at" target="_blank" rel="noopener external">business.vipach.at</a></div>
    </div></footer>'''

def shell(title,description,canonical,body,schema,prefix="../"):
    return f'''<!doctype html><html lang="hu-AT"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<link rel="icon" href="https://diaszpora.kozpontiszovetseg.at/favicon.svg" type="image/svg+xml"><title>{esc(title)}</title><meta name="description" content="{esc(description)}">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="https://diaszpora.kozpontiszovetseg.at/og-diaszpora.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:type" content="image/jpeg"><meta name="twitter:image" content="https://diaszpora.kozpontiszovetseg.at/og-diaszpora.jpg"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(description)}">
<link rel="stylesheet" href="{prefix}styles.css">
<script type="application/ld+json">{jsonld(schema)}</script></head><body>
<a class="skip" href="#main">Ugrás a tartalomhoz</a>
<header class="topbar"><div class="wrap navrow"><a class="brand" href="{prefix}"><span class="mark">AT×HU</span><span>Magyar Programok Ausztriában</span></a><nav><a href="{prefix}#terkep">Térkép</a><a href="{prefix}#szervezetek">Közösségek</a><a href="{prefix}#oktatas">Oktatás</a><a href="{prefix}#naptar">Programok</a></nav></div></header>
<main id="main">{body}</main>{footer(prefix)}<script src="{prefix}ui.js?v=20260926-consent-nav" defer></script></body></html>'''

def place_schema(e):
    addr=e.get("address")
    venue=e.get("venue")
    city=e.get("city")
    if not (addr or venue or city): return None
    address={"@type":"PostalAddress","addressCountry":"AT"}
    if addr: address["streetAddress"]=addr
    if city: address["addressLocality"]=city
    return {"@type":"Place","name":venue or city or addr,"address":address}

def offer_schema(e):
    if not (e.get("registrationUrl") or e.get("price") is not None): return None
    x={"@type":"Offer"}
    if e.get("registrationUrl"): x["url"]=e["registrationUrl"]
    if e.get("price") is not None: x["price"]=str(e["price"])
    if e.get("priceCurrency"): x["priceCurrency"]=e["priceCurrency"]
    if e.get("availability"): x["availability"]=e["availability"]
    return x

for e in events:
    oid=e.get("organizationId")
    org=org_by_id.get(oid,{})
    url=f'{BASE}/esemenyek/{quote(e["id"])}.html'
    location=place_schema(e)
    schema_event={
      "@type":"Event","@id":url+"#event","name":e.get("name"),"startDate":e.get("startDate"),
      "url":url,"description":e.get("description") or f'{e.get("name")} – {org.get("name") or e.get("organizer") or "magyar közösségi program"}',
      "inLanguage":"hu-AT",
      "organizer":{"@type":"Organization","name":org.get("name") or e.get("organizer"),"url":f'{BASE}/szervezetek/{quote(oid)}.html' if oid else None}
    }
    if e.get("endDate"): schema_event["endDate"]=e["endDate"]
    if location: schema_event["location"]=location
    if e.get("eventStatus"): schema_event["eventStatus"]=e["eventStatus"]
    if e.get("attendanceMode"): schema_event["eventAttendanceMode"]=e["attendanceMode"]
    if e.get("image"): schema_event["image"]=[e["image"]]
    if e.get("performers"): schema_event["performer"]=[{"@type":"Person","name":x} for x in e["performers"]]
    offer=offer_schema(e)
    if offer: schema_event["offers"]=offer
    schema={"@context":"https://schema.org","@graph":[
      {"@type":"WebPage","@id":url+"#page","url":url,"name":e.get("name"),"inLanguage":"hu-AT","mainEntity":{"@id":url+"#event"},"isPartOf":{"@id":BASE+"/#website"},"publisher":{"@id":BASE+"/#publisher"},**({"dateModified":str(e.get("verifiedAt"))[:10]} if e.get("verifiedAt") else {})},
      schema_event,
      PUBLISHER,
      {"@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"Magyar Programok Ausztriában","item":BASE+"/"},
        {"@type":"ListItem","position":2,"name":"Programok","item":BASE+"/#naptar"},
        {"@type":"ListItem","position":3,"name":e.get("name"),"item":url}
      ]}
    ]}
    details=[]
    if e.get("startDate"): details.append(f'<p><strong>Kezdés:</strong> {esc(e.get("startDate"))}</p>')
    if e.get("endDate"): details.append(f'<p><strong>Vége:</strong> {esc(e.get("endDate"))}</p>')
    if e.get("venue") or e.get("address"): details.append(f'<p><strong>Helyszín:</strong> {esc(" · ".join(x for x in [e.get("venue"),e.get("address")] if x))}</p>')
    if e.get("description"): details.append(f'<p>{esc(e.get("description"))}</p>')
    if e.get("performers"): details.append(f'<p><strong>Fellépők / közreműködők:</strong> {esc(", ".join(e.get("performers")))}</p>')
    if e.get("price") is not None: details.append(f'<p><strong>Ár:</strong> {esc(e.get("price"))} {esc(e.get("priceCurrency") or "")}</p>')
    links=[]
    if e.get("registrationUrl"): links.append(f'<a class="btn primary" href="{esc(e.get("registrationUrl"))}" target="_blank" rel="noopener external">Regisztráció / jegy ↗</a>')
    if e.get("sourceUrl"): links.append(f'<a class="btn" href="{esc(e.get("sourceUrl"))}" target="_blank" rel="noopener external">Hivatalos forrás ↗</a>')
    if oid: links.append(f'<a class="btn" href="../szervezetek/{esc(oid)}.html">Szervező profilja →</a>')
    body=f'''<section class="hero"><div class="wrap"><div class="eyebrow">Program · {esc(states.get(e.get("state"),{}).get("name") or e.get("state"))}</div><h1>{esc(e.get("name"))}</h1><p class="lead">{esc(org.get("name") or e.get("organizer") or "")}</p><div class="hero-actions">{"".join(links)}</div></div></section>
<section class="section"><div class="wrap trust-grid"><div><h2>Programinformáció</h2></div><div>{"".join(details)}</div></div></section>'''
    (EVENT_DIR/f'{e["id"]}.html').write_text(shell(f'{e.get("name")} | Magyar program Ausztriában',schema_event["description"],url,body,schema),encoding="utf-8")

for sid,s in states.items():
    s_org=[o for o in orgs if o.get("state")==sid]
    s_edu=[x for x in education if x.get("state")==sid]
    s_ev=[e for e in events if e.get("state")==sid]
    url=f"{BASE}/tartomanyok/{sid}.html"
    desc=f'{s["name"]} magyar szervezetei, oktatási lehetőségei és ellenőrzött programjai egy forrásalapú címtárban.'
    items=[]
    pos=1
    for o in s_org:
        items.append({"@type":"ListItem","position":pos,"url":f'{BASE}/szervezetek/{quote(o["id"])}.html',"name":o["name"]});pos+=1
    schema={"@context":"https://schema.org","@graph":[
      {"@type":"CollectionPage","@id":url+"#page","url":url,"name":f'{s["name"]} magyar közösségei és programjai',"description":desc,"inLanguage":"hu-AT","isPartOf":{"@id":BASE+"/#website"},"publisher":{"@id":BASE+"/#publisher"},"mainEntity":{"@id":url+"#list"}},
      {"@type":"ItemList","@id":url+"#list","numberOfItems":len(items),"itemListElement":items},
      PUBLISHER,
      {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Magyar Programok Ausztriában","item":BASE+"/"},{"@type":"ListItem","position":2,"name":s["name"],"item":url}]}
    ]}
    cards="".join(f'<article class="card"><div class="meta">{esc(o.get("city"))} · {esc(o.get("type"))}</div><h3><a href="../szervezetek/{esc(o["id"])}.html">{esc(o["name"])}</a></h3><p>{esc(o.get("intro"))}</p></article>' for o in s_org)
    body=f'''<section class="hero"><div class="wrap"><div class="eyebrow">Tartományi tudásoldal</div><h1>{esc(s["name"])}</h1><p class="lead">{esc(desc)}</p></div></section>
<section class="section"><div class="wrap"><div class="section-head"><div><h2>{len(s_org)} közösség · {len(s_edu)} oktatási hely · {len(s_ev)} aktuális program</h2><p>Az itt szereplő rekordok forrásai a profiloldalakon külön ellenőrizhetők.</p></div></div><div class="cards">{cards}</div></div></section>'''
    (STATE_DIR/f"{sid}.html").write_text(shell(f'{s["name"]} magyar közösségei, iskolái és programjai',desc,url,body,schema),encoding="utf-8")

for c in categories:
    cid=c["id"]; label=c["label"]
    selected=[o for o in orgs if cid in (o.get("categories") or [])]
    url=f"{BASE}/kategoriak/{cid}.html"
    desc=f'{label} kategóriába tartozó ausztriai magyar szervezetek és közösségek ellenőrzött forrásokkal.'
    items=[{"@type":"ListItem","position":i+1,"url":f'{BASE}/szervezetek/{quote(o["id"])}.html',"name":o["name"]} for i,o in enumerate(selected)]
    schema={"@context":"https://schema.org","@graph":[
      {"@type":"CollectionPage","@id":url+"#page","url":url,"name":f'{label} – ausztriai magyar közösségek',"description":desc,"inLanguage":"hu-AT","isPartOf":{"@id":BASE+"/#website"},"publisher":{"@id":BASE+"/#publisher"},"mainEntity":{"@id":url+"#list"}},
      {"@type":"ItemList","@id":url+"#list","numberOfItems":len(items),"itemListElement":items},PUBLISHER,
      {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Magyar Programok Ausztriában","item":BASE+"/"},{"@type":"ListItem","position":2,"name":label,"item":url}]}
    ]}
    cards="".join(f'<article class="card"><div class="meta">{esc(states.get(o.get("state"),{}).get("name"))} · {esc(o.get("city"))}</div><h3><a href="../szervezetek/{esc(o["id"])}.html">{esc(o["name"])}</a></h3><p>{esc(o.get("intro"))}</p></article>' for o in selected)
    body=f'''<section class="hero"><div class="wrap"><div class="eyebrow">Tematikus tudásoldal</div><h1>{esc(label)}</h1><p class="lead">{esc(desc)}</p></div></section>
<section class="section"><div class="wrap"><div class="section-head"><div><h2>{len(selected)} közösség</h2><p>Nem kulcsszóhalmozás: csak a címtárban ténylegesen ebbe a kategóriába sorolt szervezetek jelennek meg.</p></div></div><div class="cards">{cards}</div></div></section>'''
    (CATEGORY_DIR/f"{cid}.html").write_text(shell(f'{label} | Ausztriai magyar közösségek',desc,url,body,schema),encoding="utf-8")

entity={
 "@context":"https://schema.org",
 "@graph":[
   {"@type":"WebSite","@id":BASE+"/#website","name":"Magyar Programok Ausztriában","url":BASE+"/","inLanguage":"hu-AT","publisher":{"@id":BASE+"/#publisher"}},
   PUBLISHER,
   {"@type":"Dataset","@id":BASE+"/#dataset","name":"Ausztriai magyar szervezetek, oktatás és programok","description":"Forrásalapú országos adatbázis az Ausztriában működő magyar közösségekről, oktatási helyekről és nyilvános eseményekről.","url":BASE+"/","inLanguage":"hu-AT","creator":{"@id":BASE+"/#publisher"},"license":BASE+"/forrasok.html","dateModified":DATA_MODIFIED,"spatialCoverage":{"@type":"Country","name":"Austria"},"keywords":["ausztriai magyarok","magyar szervezetek Ausztriában","magyar programok Ausztriában","magyar oktatás Ausztriában","diaszpóra"],
    "distribution":[
      {"@type":"DataDownload","encodingFormat":"application/json","contentUrl":BASE+"/data/organizations.json"},
      {"@type":"DataDownload","encodingFormat":"application/json","contentUrl":BASE+"/data/education.json"},
      {"@type":"DataDownload","encodingFormat":"application/json","contentUrl":BASE+"/data/events.json"},
      {"@type":"DataDownload","encodingFormat":"application/json","contentUrl":BASE+"/data/articles.json"}
    ]}
 ]}
(ROOT/"entity.jsonld").write_text(json.dumps(entity,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

ai_entry={
 "name":"Magyar Programok Ausztriában",
 "canonical":BASE+"/",
 "language":"hu-AT",
 "publisher":{"name":PUBLISHER["name"],"url":PUBLISHER["url"],"zvr":"079797621"},
 "purpose":"Forrásalapú országos referencia-adatbázis ausztriai magyar szervezetekhez, oktatáshoz és nyilvános programokhoz.",
 "updated":{"organizations":ORG.get("updated"),"education":EDU.get("updated"),"events":EV.get("updated")},
 "counts":{"organizations":len(orgs),"education":len(education),"events":len(events),"states":len(states),"categories":len(categories)},
 "canonicalData":{
   "organizations":BASE+"/data/organizations.json","education":BASE+"/data/education.json","events":BASE+"/data/events.json","articles":BASE+"/data/articles.json",
   "entityGraph":BASE+"/entity.jsonld","methodology":BASE+"/forrasok.html","dataQuality":BASE+"/adatminoseg.html","llms":BASE+"/llms.txt","aiTrust":BASE+"/ai.txt","sitemap":BASE+"/sitemap.xml"
 },
 "citationPolicy":"Állítást csak canonical adatból vagy a rekordhoz kapcsolt bizonyító/hivatalos forrásból vezess le; hiányzó tényt ne következtess."
}
(ROOT/"ai-entry.json").write_text(json.dumps(ai_entry,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def status_counts(rows):
    out={}
    for r in rows:
        k=r.get("status") or "unknown"
        out[k]=out.get(k,0)+1
    return out

event_health=status_counts(SOURCE_HEALTH.get("sources",[]))
edu_health=status_counts(EDU_HEALTH.get("sites",[]))
quality_url=BASE+"/adatminoseg.html"
quality_desc="A DORAPP forrás-, frissességi és adatminőségi státuszának nyilvános, géppel is értelmezhető összefoglalója."
quality_schema={"@context":"https://schema.org","@graph":[
  {"@type":"WebPage","@id":quality_url+"#page","url":quality_url,"name":"DORAPP adatminőség és transzparencia","description":quality_desc,"inLanguage":"hu-AT","isPartOf":{"@id":BASE+"/#website"},"publisher":{"@id":BASE+"/#publisher"}},
  {"@type":"DataCatalog","@id":quality_url+"#catalog","name":"DORAPP – Ausztriai magyar közösségi adatbázis","url":BASE+"/","description":quality_desc,"provider":{"@id":BASE+"/#publisher"},"dataset":{"@id":BASE+"/#dataset"},"dateModified":DATA_MODIFIED},
  PUBLISHER
]}
event_rows="".join(f'<li><strong>{esc(k)}</strong>: {v}</li>' for k,v in sorted(event_health.items()))
edu_rows="".join(f'<li><strong>{esc(k)}</strong>: {v}</li>' for k,v in sorted(edu_health.items()))
quality_body=f'''<section class="hero"><div class="wrap"><div class="eyebrow">Transzparencia · E‑E‑A‑T · AI Trust</div><h1>Adatminőség és frissesség.</h1><p class="lead">{esc(quality_desc)}</p></div></section>
<section class="section"><div class="wrap trust-grid"><div><h2>Aktuális lefedettség</h2></div><div><p><strong>{len(orgs)}</strong> szervezet és közösség<br><strong>{len(education)}</strong> oktatási rekord<br><strong>{len(events)}</strong> nyilvántartott, forrással rendelkező esemény<br><strong>{len(states)}</strong> osztrák tartomány</p><p>Szervezeti adat frissítve: {esc(ORG.get("updated"))}<br>Oktatási adat frissítve: {esc(EDU.get("updated"))}<br>Eseményadat frissítve: {esc(EV.get("updated"))}</p></div></div></section>
<section class="section muted"><div class="wrap trust-grid"><div><h2>Eseményforrás-audit</h2></div><div><ul class="source-list">{event_rows}</ul><p>A technikai hiba nem jelenti automatikusan azt, hogy a forrás vagy a szervezet megszűnt. 403/429, TLS-, DNS- és timeout-hibát külön technikai állapotként kezelünk.</p></div></div></section>
<section class="section"><div class="wrap trust-grid"><div><h2>Oktatási webaudit</h2></div><div><ul class="source-list">{edu_rows}</ul><p>A saját honlapon nem talált kulcsszó nem írja felül az intézményi, hatósági vagy közszolgálati forrásból igazolt magyar oktatást.</p></div></div></section>
<section class="section muted"><div class="wrap trust-grid"><div><h2>Szerkesztési elv</h2></div><div><p>Hiányzó történeti, tagsági, kapcsolati vagy eseményadatot nem következtetünk. A strukturált profilmezők steward‑ellenőrzéssel, forrás alapján bővülnek; az automata esemény- és sajtófelderítés nem írhatja felül ezeket.</p><p><a href="forrasok.html">Teljes módszertan →</a><br><a href="mailto:marketing@kozpontiszovetseg.at">Hibajelentés / korrekció →</a></p></div></div></section>'''
(ROOT/"adatminoseg.html").write_text(shell("DORAPP adatminőség és transzparencia",quality_desc,quality_url,quality_body,quality_schema,prefix=""),encoding="utf-8")

print(f"events={len(events)} states={len(states)} categories={len(categories)} entity=1 ai_entry=1 quality=1")
