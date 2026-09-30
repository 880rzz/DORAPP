#!/usr/bin/env python3
import json,html
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
BASE="https://diaszpora.kozpontiszovetseg.at"

def read(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return d

def esc(v): return html.escape(str(v or ""),quote=True)

def non_at_entities(iso):
    p=DATA/"countries"/iso
    org=read(p/"organizations.json",{"organizations":[]})
    edu=read(p/"education.json",{"institutions":[]})
    ev=read(p/"events.json",{"events":[]})
    orgs=org.get("organizations",[])
    edus=edu.get("institutions",edu.get("education",edu.get("items",[])))
    events=ev.get("events",ev.get("items",[]))
    return orgs,edus,events

def entity_sections(iso,orgs,edus):
    groups={}
    for o in orgs:
        region=o.get("region") or ("Országos" if o.get("scope")=="national" else "Régió nélkül")
        groups.setdefault(region,{"org":[],"edu":[]})["org"].append(o)
    for e in edus:
        region=e.get("region") or "Régió nélkül"
        groups.setdefault(region,{"org":[],"edu":[]})["edu"].append(e)
    out=[]
    for region in sorted(groups,key=lambda x:x.casefold()):
        block=groups[region]
        org_html="".join(
            f'<li><a href="#kozossegek"><strong>{esc(o.get("name"))}</strong></a>'
            f'<span>{esc(o.get("city") or "országos")} · {esc(o.get("type") or "szervezet")}</span></li>'
            for o in sorted(block["org"],key=lambda x:str(x.get("name","")).casefold())
        )
        edu_html="".join(
            f'<li><a href="#oktatas"><strong>{esc(e.get("name"))}</strong></a>'
            f'<span>{esc(e.get("city") or "")} · {esc(e.get("type") or "oktatás")}</span></li>'
            for e in sorted(block["edu"],key=lambda x:str(x.get("name","")).casefold())
        )
        inner=""
        if org_html:
            inner+=f'<h3>Közösségek és szervezetek</h3><ul class="country-entity-list">{org_html}</ul>'
        if edu_html:
            inner+=f'<h3>Oktatás</h3><ul class="country-entity-list">{edu_html}</ul>'
        out.append(f'<section class="country-region"><h2>{esc(region)}</h2>{inner}</section>')
    return "".join(out)

def org_cards(orgs):
    if not orgs:
        return '<div class="empty">Jelenleg nincs publikálható, ellenőrzött közösségi rekord.</div>'
    return '<div class="cards">'+''.join(
        f'<article class="card"><div class="meta">{esc(o.get("region") or "Országos")} · {esc(o.get("city") or "országos")}</div>'
        f'<h3>{esc(o.get("name"))}</h3><p>{esc(o.get("summary") or o.get("intro") or o.get("type") or "Magyar diaszpóra-entitás")}</p>'
        f'<div class="links"><a href="organizations/{esc(o.get("id"))}.html">Részletek →</a>'
        + (f'<a href="{esc(o.get("website"))}" target="_blank" rel="noopener external">Hivatalos oldal ↗</a>' if o.get("website") else '')
        + '</div></article>'
        for o in sorted(orgs,key=lambda x:str(x.get("name","")).casefold())
    )+'</div>'

def edu_cards(edus):
    if not edus:
        return '<div class="empty">Jelenleg nincs publikálható, ellenőrzött oktatási rekord.</div>'
    return '<div class="cards">'+''.join(
        f'<article class="card"><div class="meta">{esc(e.get("region") or "Régió nélkül")} · {esc(e.get("city") or "")}</div>'
        f'<h3>{esc(e.get("name"))}</h3><p>{esc(e.get("summary") or e.get("type") or "Magyar oktatási lehetőség")}</p>'
        f'<div class="links"><a href="education/{esc(e.get("id"))}.html">Részletek →</a>'
        + (f'<a href="{esc(e.get("website"))}" target="_blank" rel="noopener external">Hivatalos oldal ↗</a>' if e.get("website") else '')
        + '</div></article>'
        for e in sorted(edus,key=lambda x:str(x.get("name","")).casefold())
    )+'</div>'

def event_cards(events):
    if not events:
        return '<div class="empty">Nincs jelenleg publikálható, ellenőrzött aktuális esemény.</div>'
    return '<div class="event-grid">'+''.join(
        f'<article class="event"><div class="date">{esc(e.get("startDate") or e.get("date") or "")}</div>'
        f'<h3>{esc(e.get("name") or e.get("title"))}</h3><p>{esc(e.get("organizer") or "")}'
        + (f'<br>{esc(e.get("venue") or e.get("city") or "")}' if (e.get("venue") or e.get("city")) else '')
        + '</p><div class="event-links">'
        + (f'<a href="{esc(e.get("sourceUrl"))}" target="_blank" rel="noopener external">Eredeti forrás ↗</a>' if e.get("sourceUrl") else '')
        + '</div></article>'
        for e in sorted(events,key=lambda x:str(x.get("startDate") or x.get("date") or ""))
    )+'</div>'

g=json.loads((DATA/"global.json").read_text(encoding="utf-8"))
for c in g.get("countries",[]):
    iso=c["iso2"]; out=ROOT/"countries"/iso; out.mkdir(parents=True,exist_ok=True)
    names=c.get("name",{}); name=names.get("hu") or names.get("en") or iso.upper()
    counts=c.get("counts",{})
    body_sections=""
    if iso=="at":
        org=json.loads((DATA/"countries"/iso/"organizations.json").read_text(encoding="utf-8"))
        states=org.get("states",[])
        state_html="".join(f'<li><a href="../../#terkep">{esc(s.get("name",""))}</a></li>' for s in states)
        legacy_links='''<a class="choice-card primary-choice" href="../../#naptar"><span>01</span><strong>Programot keresek</strong><small>Aktuális események Ausztriában.</small></a><a class="choice-card" href="../../#oktatas"><span>02</span><strong>Magyar oktatást keresek</strong><small>Óvodától az egyetemig.</small></a><a class="choice-card" href="../../#szervezetek"><span>03</span><strong>Közösséget keresek</strong><small>Kapcsolódási pontok országszerte.</small></a>'''
        body_sections=f'<section id="teruleti-attekintes" class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Országadatbázis</div><h2>Területi áttekintés</h2></div></div><ul class="country-region-list">{state_html}</ul><p class="muted">A részletes ausztriai rendszer a főoldalon érhető el.</p><p><a class="btn primary" href="../../#kereso">Ausztria teljes rendszerének megnyitása →</a></p></div></section>'
    else:
        orgs,edus,events=non_at_entities(iso)
        legacy_links='''<a class="choice-card primary-choice" href="#programok"><span>01</span><strong>Programot keresek</strong><small>Aktuális, ellenőrzött események.</small></a><a class="choice-card" href="#oktatas"><span>02</span><strong>Magyar oktatást keresek</strong><small>Iskolák és oktatási lehetőségek.</small></a><a class="choice-card" href="#kozossegek"><span>03</span><strong>Közösséget keresek</strong><small>Szervezetek és kapcsolódási pontok.</small></a>'''
        regions=entity_sections(iso,orgs,edus) or '<p class="muted">Ehhez az országhoz még nincs publikálható, ellenőrzött entitás. Ez nem jelenti azt, hogy nincs magyar közösség.</p>'
        body_sections=(
            f'<section id="teruleti-attekintes" class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Országadatbázis</div><h2>Területi áttekintés</h2><p>Régiók szerint is böngészhető, ugyanazzal a logikával, mint az ausztriai rendszer.</p></div></div>{regions}</div></section>'
            f'<section id="kozossegek" class="section muted"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Közösségek</div><h2>Közösségek és szervezetek.</h2><p>Csak publikálható, forrással igazolt diaszpóra-entitások.</p></div></div>{org_cards(orgs)}</div></section>'
            f'<section id="oktatas" class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Magyar oktatás</div><h2>Magyar oktatás.</h2><p>Ellenőrzött iskolák, hétvégi iskolák és intézményi programok.</p></div></div>{edu_cards(edus)}</div></section>'
            f'<section id="programok" class="section muted"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Programok</div><h2>Programok.</h2><p>Aktuális események, elsődleges vagy hiteles forrással.</p></div></div>{event_cards(events)}</div></section>'
        )

    title=f"Magyar közösségek – {name} | DORAPP"
    canonical=f"{BASE}/countries/{iso}/"
    schema={"@context":"https://schema.org","@type":"CollectionPage","name":title,"url":canonical,"isPartOf":{"@id":BASE+"/#website"},"about":{"@type":"Country","name":names.get("en") or name}}
    doc=f'''<!doctype html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><link rel="icon" href="../../favicon.svg" type="image/svg+xml"><title>{esc(title)}</title><meta name="description" content="{esc(name)} magyar közösségeinek, szervezeteinek, oktatásának és eseményeinek forrásalapú DORAPP országoldala."><meta name="robots" content="index,follow"><link rel="canonical" href="{canonical}"><link rel="stylesheet" href="../../styles.css"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False)}</script></head><body><a class="skip" href="#content">Ugrás a tartalomhoz</a><header class="topbar"><div class="wrap navrow"><a class="brand" href="../../"><span class="mark">HU</span><span>DORAPP</span></a><nav><a href="../../">Világ</a><a href="../../#kereso">Globális kereső</a></nav></div></header><main id="content"><section class="hero"><div class="wrap"><div class="eyebrow">DORAPP · {iso.upper()}</div><h1>{esc(name)} <span>magyar közösségei</span></h1><p class="lead">{counts.get("organizations",0)} szervezet, {counts.get("education",0)} oktatási rekord és {counts.get("events",0)} esemény a jelenlegi ellenőrzött adatállapot szerint.</p><div class="choice-grid country-choice-grid" aria-label="Mit keresel?">{legacy_links}</div><p class="hero-proof"><strong>Forrásalapú országadatbázis.</strong> Kutatási állapot: {esc(c.get("researchStatus","unresearched"))}.</p></div></section>{body_sections}</main><footer><div class="wrap footer-grid"><div><b>DORAPP</b><p>Forrásalapú magyar diaszpóra-címtár és programnaptár.</p></div><div><a href="../../forrasok.html">Hogyan működik?</a><br><a href="../../adatminoseg.html">Adatminőség és transzparencia</a></div><div><a href="https://www.kozpontiszovetseg.at/kapcsolat" target="_blank" rel="noopener external">Impresszum / kapcsolat ↗</a><br><a href="https://www.kozpontiszovetseg.at/post/gdpr-ai-trust" target="_blank" rel="noopener external">GDPR & AI Trust ↗</a></div></div></footer><script src="../../ui.js?v=20260926-consent-nav" defer></script></body></html>'''
    (out/"index.html").write_text(doc,encoding="utf-8")
print(f"Generated {len(g.get('countries',[]))} country routes")
