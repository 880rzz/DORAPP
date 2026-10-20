#!/usr/bin/env python3
import html
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
BASE="https://www.diaszporaterkep.hu"

def read(path,default):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return default

def esc(value):
    return html.escape(str(value or ""),quote=True)

def evidence_rows(items):
    rows=[]
    for item in items or []:
        if not isinstance(item,dict) or not item.get("url"): continue
        rows.append(f'<li><a href="{esc(item["url"])}" target="_blank" rel="noopener external">{esc(item.get("label") or "Ellenőrző forrás")} ↗</a></li>')
    return "".join(rows)

def main():
    registry=read(DATA/"global.json",{"countries":[]})
    generated=0
    for country in registry.get("countries",[]):
        iso=country["iso2"]
        source=DATA/"countries"/iso/"education.json"
        if not source.exists(): continue
        doc=read(source,{"institutions":[]})
        org_doc=read(DATA/"countries"/iso/"organizations.json",{"states":[]})
        region_labels={str(x.get("id")):str(x.get("name") or x.get("id")) for x in (org_doc.get("states") or org_doc.get("regions") or []) if x.get("id")}
        country_name=country.get("name",{}).get("hu") or country.get("name",{}).get("en") or iso.upper()
        modified=doc.get("updated") or country.get("lastBroadVerifiedAt") or country.get("lastResearchAttemptAt")
        for item in doc.get("institutions",doc.get("education",doc.get("items",[]))):
            entity_id=item.get("id")
            if not entity_id or not item.get("name"): continue
            output=ROOT/"countries"/iso/"education"
            output.mkdir(parents=True,exist_ok=True)
            url=f"{BASE}/countries/{iso}/education/{entity_id}.html"
            country_url=f"{BASE}/countries/{iso}/"
            title=f"{item['name']} | DORAPP"
            description=item.get("summary") or item.get("intro") or f"{item['name']} ellenőrzött magyar oktatási adatlapja {country_name} területén."
            verified=item.get("verifiedAt") or modified
            address={"@type":"PostalAddress","addressCountry":iso.upper()}
            if item.get("city"): address["addressLocality"]=item["city"]
            if item.get("region"): address["addressRegion"]=region_labels.get(str(item["region"]),item["region"])
            entity={"@type":"EducationalOrganization","@id":url+"#entity","name":item["name"],"description":description,"address":address,"areaServed":{"@type":"Country","name":country_name},"mainEntityOfPage":{"@id":url+"#page"}}
            if item.get("website"): entity["url"]=item["website"]
            schema={"@context":"https://schema.org","@graph":[
                {"@type":"ProfilePage","@id":url+"#page","url":url,"name":title,"description":description,"inLanguage":"hu","dateModified":verified,"mainEntity":{"@id":url+"#entity"},"isPartOf":{"@id":BASE+"/#website"},"publisher":{"@id":BASE+"/#organization"}},
                entity,
                {"@type":"BreadcrumbList","@id":url+"#breadcrumb","itemListElement":[
                    {"@type":"ListItem","position":1,"name":"DORAPP","item":BASE+"/"},
                    {"@type":"ListItem","position":2,"name":country_name,"item":country_url},
                    {"@type":"ListItem","position":3,"name":item["name"],"item":url},
                ]},
            ]}
            evidence=[entry for entry in item.get("evidenceSources",[]) if isinstance(entry,dict) and entry.get("url")]
            actions=[]
            if item.get("website"):
                actions.append(f'<a class="btn primary" href="{esc(item["website"])}" target="_blank" rel="noopener external">Hivatalos oldal ↗</a>')
            elif evidence:
                actions.append(f'<a class="btn primary" href="{esc(evidence[0]["url"])}" target="_blank" rel="noopener external">Elsődleges forrás ↗</a>')
            operator=""
            operator_id=item.get("operatorId")
            if operator_id:
                org_profile=ROOT/"countries"/iso/"organizations"/f"{operator_id}.html"
                value=(f'<a href="../organizations/{esc(operator_id)}.html">{esc(operator_id)}</a>' if org_profile.exists() else esc(operator_id))
                operator=f'<p><strong>Kapcsolódó szervezet:</strong> {value}</p>'
            source_list=evidence_rows(evidence) or "<li>Nincs külön nyilvános forrás megadva.</li>"
            place=" · ".join(str(value) for value in [region_labels.get(str(item.get("region")),item.get("region")),item.get("city"),"Oktatás"] if value)
            body=f'''<!doctype html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><link rel="icon" href="../../../favicon.svg" type="image/svg+xml"><title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="author" content="Központi Szövetség"><meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large"><link rel="canonical" href="{url}"><link rel="alternate" type="text/plain" href="../../../llms.txt" title="LLM információ"><meta property="og:type" content="profile"><meta property="og:site_name" content="DORAPP"><meta property="og:title" content="{esc(item['name'])}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{url}"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="{esc(item['name'])}"><meta name="twitter:description" content="{esc(description)}"><link rel="stylesheet" href="../../../styles.css?v=20261015-quality-1"><link rel="stylesheet" href="/design-editorial.css?v=20261015-2"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace("</","<\\/")}</script></head><body><a class="skip" href="#content">Ugrás a tartalomhoz</a><header class="topbar"><div class="wrap navrow"><a class="brand" href="../"><span class="mark">HU</span><span>DORAPP · {esc(country_name)}</span></a><nav><a href="../#terkep">Térkép</a><a href="../#kereso">Kereső</a><a href="../#kozossegek">Szervezetek</a><a href="../#oktatas">Oktatás</a><a href="../#programok">Programok</a></nav></div></header><main id="content"><section class="hero"><div class="wrap"><div class="eyebrow">{esc(place)}</div><h1>{esc(item['name'])}</h1><p class="lead">{esc(description)}</p><div class="hero-actions">{"".join(actions)}</div></div></section><section class="section"><div class="wrap trust-grid"><div><h2>Oktatási adatok</h2></div><div><p><strong>Város:</strong> {esc(item.get("city") or "Nincs megadva")}<br><strong>Régió:</strong> {esc(region_labels.get(str(item.get("region")),item.get("region")) or "Nincs megadva")}<br><strong>Típus:</strong> <span title="{esc(item.get("type") or "Oktatás")}">Oktatás</span></p>{operator}</div></div></section><section class="section muted"><div class="wrap trust-grid"><div><h2>Források és ellenőrzés</h2></div><div><p>A profilt a DORAPP nyilvános források alapján tartja karban.{(' Utolsó adatellenőrzés: <time datetime="'+esc(verified)+'">'+esc(verified)+'</time>.' if verified else '')}</p><ul class="source-list">{source_list}</ul><p><a href="{url}">Állandó DORAPP-adatlap</a> · <a href="../../../forrasok.html">Forráskezelés és módszertan</a></p></div></div></section></main><footer><div class="wrap footer-grid"><div><b>DORAPP</b><p>Forrásalapú magyar diaszpóra-címtár és programnaptár.</p></div><div><a href="../">Vissza {esc(country_name)} országoldalára</a></div><div><a href="../../../adatminoseg.html">Adatminőség</a></div><div class="site-credit">A <a href="https://www.magyariskola.at/" target="_blank" rel="noopener external">Bécsi Magyar Iskola</a> – <a href="https://rolunk.at/aktualis/a-fiataloknak-ma-mar-bizonyitek-kell-egy-becsi-kreativ-kozosseg-uj-generaciot-epit/" target="_blank" rel="noopener external">Be Smart Kids Club</a> csapata hozta létre.<br><a href="mailto:marketing@kozpontiszovetseg.at">marketing@kozpontiszovetseg.at</a></div></div></footer><script src="../../../ui.js?v=20261015-trust-contact-1" defer></script></body></html>'''
            (output/f"{entity_id}.html").write_text(body,encoding="utf-8")
            generated+=1
    print(f"Generated worldwide education profiles={generated}")

if __name__=="__main__":
    main()
