#!/usr/bin/env python3
import json, html
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
BASE="https://diaszpora.kozpontiszovetseg.at"

def read(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return d

def main():
    g=read(DATA/"global.json",{"countries":[]})
    generated=0
    for c in g.get("countries",[]):
        iso=c["iso2"]
        doc=read(DATA/"countries"/iso/"organizations.json",{"organizations":[]})
        for o in doc.get("organizations",[]):
            eid=o.get("id")
            if not eid:
                continue

            out=ROOT/"countries"/iso/"organizations"
            out.mkdir(parents=True,exist_ok=True)
            url=f"{BASE}/countries/{iso}/organizations/{eid}.html"
            country_name=c.get("name",{}).get("hu") or c.get("name",{}).get("en") or iso.upper()
            title=f"{o.get('name')} | DORAPP"
            desc=f"{o.get('name')} – ellenőrzött magyar diaszpóra-szervezeti profil {country_name} területén."

            entity={"@type":"Organization","@id":url+"#entity","name":o.get("name")}
            if o.get("website"):
                entity["url"]=o["website"]
            address={"@type":"PostalAddress","addressCountry":iso.upper()}
            if o.get("city"): address["addressLocality"]=o["city"]
            if o.get("region"): address["addressRegion"]=o["region"]
            entity["address"]=address

            schema={"@context":"https://schema.org","@graph":[
              {"@type":"ProfilePage","@id":url+"#page","url":url,"name":title,"mainEntity":{"@id":url+"#entity"}},
              entity,
              {"@type":"BreadcrumbList","itemListElement":[
                {"@type":"ListItem","position":1,"name":"DORAPP","item":BASE+"/"},
                {"@type":"ListItem","position":2,"name":country_name,"item":f"{BASE}/countries/{iso}/"},
                {"@type":"ListItem","position":3,"name":o.get("name"),"item":url}
              ]}
            ]}

            evidence=[e for e in o.get("evidenceSources",[]) if e.get("url")]
            sources="".join(
                f'<li><a href="{html.escape(e.get("url",""))}" target="_blank" rel="noopener external">{html.escape(e.get("label","Forrás"))} ↗</a></li>'
                for e in evidence
            )
            primary=o.get("website") or (evidence[0]["url"] if evidence else None)
            if o.get("website"):
                action_label="Hivatalos oldal ↗"
            elif primary:
                action_label="Elsődleges bizonyíték ↗"
            else:
                action_label=None
            action=(f'<div class="hero-actions"><a class="btn primary" href="{html.escape(primary)}" target="_blank" rel="noopener external">{action_label}</a></div>' if primary else "")
            eyebrow=" · ".join(x for x in [str(o.get("city") or ""),str(o.get("region") or ""),("országos" if o.get("scope")=="national" else "")] if x)

            body=f'''<!doctype html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}"><meta name="robots" content="index,follow"><link rel="canonical" href="{url}"><link rel="stylesheet" href="../../../styles.css"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False)}</script></head><body><header class="topbar"><div class="wrap navrow"><a class="brand" href="../../"><span class="mark">HU</span><span>DORAPP</span></a></div></header><main><section class="hero"><div class="wrap"><div class="eyebrow">{html.escape(eyebrow)}</div><h1>{html.escape(str(o.get("name") or ""))}</h1><p class="lead">Forrásalapúan ellenőrzött magyar diaszpóra-entitás.</p>{action}</div></section><section class="section"><div class="wrap trust-grid"><div><h2>Ellenőrzött adatok</h2></div><div><p><strong>Város:</strong> {html.escape(str(o.get("city") or "országos"))}<br><strong>Régió:</strong> {html.escape(str(o.get("region") or "—"))}<br><strong>Típus:</strong> {html.escape(str(o.get("type") or "—"))}</p></div></div></section><section class="section muted"><div class="wrap trust-grid"><div><h2>Források</h2></div><div><ul class="source-list">{sources}</ul></div></div></section></main></body></html>'''
            (out/f"{eid}.html").write_text(body,encoding="utf-8")
            generated+=1

    print(f"Generated worldwide organization profiles={generated}")

if __name__=="__main__":
    main()
