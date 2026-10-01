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
    # Generated event profiles are canonical build artifacts: remove stale pages first.
    for country_dir in (ROOT/"countries").glob("*") if (ROOT/"countries").exists() else []:
        event_dir=country_dir/"events"
        if event_dir.exists():
            for path in event_dir.glob("*.html"): path.unlink()
    registry=read(DATA/"global.json",{"countries":[]})
    generated=0
    for c in registry.get("countries",[]):
        iso=c.get("iso2")
        if not iso: continue
        country_name=c.get("name",{}).get("hu") or c.get("name",{}).get("en") or iso.upper()
        doc=read(DATA/"countries"/iso/"events.json",{"events":[]})
        for e in doc.get("events",doc.get("items",[])):
            eid=e.get("id")
            name=e.get("name") or e.get("title")
            if not eid or not name: continue
            out=ROOT/"countries"/iso/"events"
            out.mkdir(parents=True,exist_ok=True)
            url=f"{BASE}/countries/{iso}/events/{eid}.html"
            title=f"{name} | DORAPP"
            desc=e.get("description") or f"{name} – ellenőrzött magyar diaszpóra-program {country_name} területén."
            event={
                "@type":"Event",
                "@id":url+"#event",
                "name":name,
                "url":url,
                "startDate":e.get("startDate") or e.get("date"),
            }
            if e.get("endDate"): event["endDate"]=e.get("endDate")
            if e.get("venue") or e.get("city"):
                event["location"]={
                    "@type":"Place",
                    "name":e.get("venue") or e.get("city"),
                    "address":{
                        "@type":"PostalAddress",
                        "addressCountry":iso.upper(),
                        **({"addressLocality":e.get("city")} if e.get("city") else {}),
                        **({"addressRegion":e.get("region")} if e.get("region") else {}),
                    }
                }
            if e.get("organizer"):
                event["organizer"]={"@type":"Organization","name":e.get("organizer")}
            schema={"@context":"https://schema.org","@graph":[
                {"@type":"WebPage","@id":url+"#page","url":url,"name":title,"mainEntity":{"@id":url+"#event"}},
                event,
                {"@type":"BreadcrumbList","itemListElement":[
                    {"@type":"ListItem","position":1,"name":"DORAPP","item":BASE+"/"},
                    {"@type":"ListItem","position":2,"name":country_name,"item":f"{BASE}/countries/{iso}/"},
                    {"@type":"ListItem","position":3,"name":name,"item":url}
                ]}
            ]}
            source=e.get("sourceUrl")
            source_link=(f'<a class="btn primary" href="{esc(source)}" target="_blank" rel="noopener external">Eredeti forrás ↗</a>' if source else "")
            details=" · ".join(x for x in [str(e.get("city") or ""),str(e.get("venue") or ""),str(e.get("organizer") or "")] if x)
            body=f'''<!doctype html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow"><link rel="canonical" href="{url}"><link rel="stylesheet" href="../../../styles.css"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False)}</script></head><body><header class="topbar"><div class="wrap navrow"><a class="brand" href="../../"><span class="mark">HU</span><span>DORAPP</span></a></div></header><main><section class="hero"><div class="wrap"><div class="eyebrow">{esc(country_name)} · {esc(e.get("startDate") or e.get("date") or "")}</div><h1>{esc(name)}</h1><p class="lead">{esc(desc)}</p><div class="hero-actions">{source_link}</div></div></section><section class="section"><div class="wrap trust-grid"><div><h2>Programadatok</h2></div><div><p>{esc(details or "Ellenőrzött eseményrekord.")}</p></div></div></section></main></body></html>'''
            (out/f"{eid}.html").write_text(body,encoding="utf-8")
            generated+=1
    print(f"Generated worldwide event profiles={generated}")

if __name__=="__main__":
    main()
