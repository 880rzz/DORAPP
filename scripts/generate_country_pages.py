#!/usr/bin/env python3
import json,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
BASE="https://diaszpora.kozpontiszovetseg.at"
g=json.loads((DATA/"global.json").read_text(encoding="utf-8"))
for c in g.get("countries",[]):
    iso=c["iso2"]; out=ROOT/"countries"/iso; out.mkdir(parents=True,exist_ok=True)
    names=c.get("name",{}); name=names.get("hu") or names.get("en") or iso.upper()
    counts=c.get("counts",{})
    if iso=="at":
        org=json.loads((DATA/"countries"/iso/"organizations.json").read_text(encoding="utf-8"))
        states=org.get("states",[])
        state_html="".join(f'<li><a href="../../#terkep">{html.escape(str(s.get("name","")))}</a></li>' for s in states)
        legacy_links='''<a class="action primary" href="../../#kereso">Keresés Ausztriában</a><a class="action" href="../../#naptar">Programok</a><a class="action" href="../../#oktatas">Oktatás</a><a class="action" href="../../#szervezetek">Közösségek</a>'''
    else:
        state_html=""; legacy_links=""
    title=f"Magyar közösségek – {name} | DORAPP"
    canonical=f"{BASE}/countries/{iso}/"
    schema={"@context":"https://schema.org","@type":"CollectionPage","name":title,"url":canonical,"isPartOf":{"@id":BASE+"/#website"},"about":{"@type":"Country","name":names.get("en") or name}}
    doc=f'''<!doctype html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><link rel="icon" href="../../favicon.svg" type="image/svg+xml"><title>{html.escape(title)}</title><meta name="description" content="{html.escape(name)} magyar közösségeinek, szervezeteinek, oktatásának és eseményeinek forrásalapú DORAPP országoldala."><meta name="robots" content="index,follow"><link rel="canonical" href="{canonical}"><link rel="stylesheet" href="../../styles.css"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False)}</script></head><body><a class="skip" href="#content">Ugrás a tartalomhoz</a><header class="topbar"><div class="wrap navrow"><a class="brand" href="../../"><span class="mark">HU</span><span>DORAPP</span></a><nav><a href="../../">Világ</a><a href="../../#kereso">Globális kereső</a></nav></div></header><main id="content"><section class="hero"><div class="wrap"><div class="eyebrow">DORAPP · {iso.upper()}</div><h1>{html.escape(name)} <span>magyar közösségei</span></h1><p class="lead">{counts.get("organizations",0)} szervezet, {counts.get("education",0)} oktatási rekord és {counts.get("events",0)} esemény a jelenlegi ellenőrzött adatállapot szerint.</p><div class="country-actions">{legacy_links}</div></div></section><section class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Országadatbázis</div><h2>Területi áttekintés</h2></div></div><ul class="country-region-list">{state_html}</ul><p class="muted">Kutatási állapot: {html.escape(str(c.get("researchStatus","unresearched")))}. A számlálók a canonical országadatokból automatikusan képződnek.</p></div></section></main><footer><div class="wrap footer-grid"><div><b>DORAPP</b><p>Forrásalapú magyar diaszpóra-címtár és programnaptár.</p></div><div><a href="../../forrasok.html">Hogyan működik?</a><br><a href="../../adatminoseg.html">Adatminőség és transzparencia</a></div><div><a href="https://www.kozpontiszovetseg.at/kapcsolat" target="_blank" rel="noopener external">Impresszum / kapcsolat ↗</a><br><a href="https://www.kozpontiszovetseg.at/post/gdpr-ai-trust" target="_blank" rel="noopener external">GDPR & AI Trust ↗</a></div></div></footer><script src="../../ui.js?v=20260926-consent-nav" defer></script></body></html>'''
    (out/"index.html").write_text(doc,encoding="utf-8")
print(f"Generated {len(g.get('countries',[]))} country routes")
