#!/usr/bin/env python3
import json, html
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
BASE="https://diaszpora.kozpontiszovetseg.at"

def read(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return d

def esc(v): return html.escape(str(v or ""),quote=True)

def main():
    g=read(DATA/"global.json",{"countries":[]})
    generated=0
    for c in g.get("countries",[]):
        iso=c["iso2"]
        if iso=="at": continue
        p=DATA/"countries"/iso/"education.json"
        if not p.exists(): continue
        doc=read(p,{"institutions":[]})
        country_name=c.get("name",{}).get("hu") or c.get("name",{}).get("en") or iso.upper()
        for x in doc.get("institutions",doc.get("education",doc.get("items",[]))):
            eid=x.get("id")
            if not eid: continue
            out=ROOT/"countries"/iso/"education"
            out.mkdir(parents=True,exist_ok=True)
            url=f"{BASE}/countries/{iso}/education/{eid}.html"
            title=f"{x.get('name')} | DORAPP"
            desc=x.get("intro") or f"{x.get('name')} – ellenőrzött magyar oktatási rekord {country_name} területén."
            entity={"@type":"EducationalOrganization","@id":url+"#entity","name":x.get("name")}
            if x.get("website"): entity["url"]=x["website"]
            entity["address"]={"@type":"PostalAddress","addressCountry":iso.upper(),**({"addressLocality":x.get("city")} if x.get("city") else {}),**({"addressRegion":x.get("region")} if x.get("region") else {})}
            schema={"@context":"https://schema.org","@graph":[
              {"@type":"ProfilePage","@id":url+"#page","url":url,"name":title,"mainEntity":{"@id":url+"#entity"}},
              entity,
              {"@type":"BreadcrumbList","itemListElement":[
                {"@type":"ListItem","position":1,"name":"DORAPP","item":BASE+"/"},
                {"@type":"ListItem","position":2,"name":country_name,"item":f"{BASE}/countries/{iso}/"},
                {"@type":"ListItem","position":3,"name":x.get("name"),"item":url}
              ]}
            ]}
            evidence=[e for e in x.get("evidenceSources",[]) if e.get("url")]
            links=[]
            if x.get("website"): links.append(f'<a class="btn primary" href="{esc(x["website"])}" target="_blank" rel="noopener external">Hivatalos oldal ↗</a>')
            elif evidence: links.append(f'<a class="btn primary" href="{esc(evidence[0]["url"])}" target="_blank" rel="noopener external">Elsődleges bizonyíték ↗</a>')
            sources="".join(f'<li><a href="{esc(e["url"])}" target="_blank" rel="noopener external">{esc(e.get("label","Forrás"))} ↗</a></li>' for e in evidence)
            operator=f'<p><strong>Fenntartó / operátor:</strong> {esc(x.get("operatorId"))}</p>' if x.get("operatorId") else ""
            body=f'''<!doctype html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow"><link rel="canonical" href="{url}"><link rel="stylesheet" href="../../../styles.css"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False)}</script></head><body><header class="topbar"><div class="wrap navrow"><a class="brand" href="../../"><span class="mark">HU</span><span>DORAPP</span></a></div></header><main><section class="hero"><div class="wrap"><div class="eyebrow">{esc(x.get("city") or "")} · {esc(x.get("region") or "")}</div><h1>{esc(x.get("name"))}</h1><p class="lead">{esc(desc)}</p><div class="hero-actions">{"".join(links)}</div></div></section><section class="section"><div class="wrap trust-grid"><div><h2>Ellenőrzött oktatási adatok</h2></div><div><p><strong>Város:</strong> {esc(x.get("city") or "—")}<br><strong>Régió:</strong> {esc(x.get("region") or "—")}<br><strong>Típus:</strong> {esc(x.get("type") or "—")}</p>{operator}</div></div></section><section class="section muted"><div class="wrap trust-grid"><div><h2>Források</h2></div><div><ul class="source-list">{sources}</ul></div></div></section></main></body></html>'''
            (out/f"{eid}.html").write_text(body,encoding="utf-8")
            generated+=1
    print(f"Generated worldwide education profiles={generated}")

if __name__=="__main__":
    main()
