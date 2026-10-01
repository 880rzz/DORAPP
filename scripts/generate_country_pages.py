#!/usr/bin/env python3
import json, html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BASE = "https://diaszpora.kozpontiszovetseg.at"
READY = {"reviewed", "verified-zero"}

def read(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def esc(value):
    return html.escape(str(value or ""), quote=True)

def country_data(iso):
    base = DATA / "countries" / iso
    org_data = read(base / "organizations.json", {"organizations":[]})
    edu_data = read(base / "education.json", {"institutions":[]})
    event_data = read(base / "events.json", {"events":[]})
    orgs = org_data.get("organizations", org_data.get("items", []))
    edus = edu_data.get("institutions", edu_data.get("education", edu_data.get("items", [])))
    events = event_data.get("events", event_data.get("items", []))
    state_names = {s.get("id"): s.get("name") for s in org_data.get("states", []) if s.get("id")}
    return orgs, edus, events, state_names

def region_name(item, state_names):
    region = item.get("region") or item.get("state")
    if region in state_names:
        return state_names[region]
    if region:
        return str(region)
    if item.get("scope") in {"national","national-and-western-europe"}:
        return "Országos"
    return "Régió nélkül"

def entity_sections(orgs, edus, state_names):
    groups = {}
    for org in orgs:
        if org.get("entityClass") == "activity":
            continue
        region = region_name(org, state_names)
        groups.setdefault(region, {"org":[], "edu":[]})["org"].append(org)
    for edu in edus:
        region = region_name(edu, state_names)
        groups.setdefault(region, {"org":[], "edu":[]})["edu"].append(edu)

    out = []
    for region in sorted(groups, key=lambda x: x.casefold()):
        block = groups[region]
        org_html = "".join(
            f'<li><a href="organizations/{esc(o.get("id"))}.html"><strong>{esc(o.get("name"))}</strong></a>'
            f'<span>{esc(o.get("city") or "országos")} · {esc(o.get("type") or "szervezet")}</span></li>'
            for o in sorted(block["org"], key=lambda x: str(x.get("name","")).casefold())
            if o.get("id") and o.get("name")
        )
        edu_html = "".join(
            f'<li><a href="education/{esc(e.get("id"))}.html"><strong>{esc(e.get("name"))}</strong></a>'
            f'<span>{esc(e.get("city") or "")} · {esc(e.get("type") or "oktatás")}</span></li>'
            for e in sorted(block["edu"], key=lambda x: str(x.get("name","")).casefold())
            if e.get("id") and e.get("name")
        )
        inner = ""
        if org_html:
            inner += f'<h3>Közösségek és szervezetek</h3><ul class="country-entity-list">{org_html}</ul>'
        if edu_html:
            inner += f'<h3>Oktatás</h3><ul class="country-entity-list">{edu_html}</ul>'
        out.append(f'<section class="country-region"><h2>{esc(region)}</h2>{inner}</section>')
    return "".join(out)

def org_cards(orgs, state_names):
    rows = [o for o in orgs if o.get("entityClass") != "activity" and o.get("id") and o.get("name")]
    if not rows:
        return '<div class="empty">Jelenleg nincs publikálható, ellenőrzött közösségi rekord.</div>'
    return '<div class="cards">' + "".join(
        f'<article class="card"><div class="meta">{esc(region_name(o,state_names))} · {esc(o.get("city") or "országos")}</div>'
        f'<h3>{esc(o.get("name"))}</h3><p>{esc(o.get("summary") or o.get("intro") or o.get("type") or "Magyar diaszpóra-entitás")}</p>'
        f'<div class="links"><a href="organizations/{esc(o.get("id"))}.html">Részletek →</a>'
        + (f'<a href="{esc(o.get("website"))}" target="_blank" rel="noopener external">Hivatalos oldal ↗</a>' if o.get("website") else "")
        + '</div></article>'
        for o in sorted(rows, key=lambda x: str(x.get("name","")).casefold())
    ) + '</div>'

def edu_cards(edus, state_names):
    rows = [e for e in edus if e.get("id") and e.get("name")]
    if not rows:
        return '<div class="empty">Jelenleg nincs publikálható, ellenőrzött oktatási rekord.</div>'
    return '<div class="cards">' + "".join(
        f'<article class="card"><div class="meta">{esc(region_name(e,state_names))} · {esc(e.get("city") or "")}</div>'
        f'<h3>{esc(e.get("name"))}</h3><p>{esc(e.get("summary") or e.get("intro") or e.get("type") or "Magyar oktatási lehetőség")}</p>'
        f'<div class="links"><a href="education/{esc(e.get("id"))}.html">Részletek →</a>'
        + (f'<a href="{esc(e.get("website"))}" target="_blank" rel="noopener external">Hivatalos oldal ↗</a>' if e.get("website") else "")
        + '</div></article>'
        for e in sorted(rows, key=lambda x: str(x.get("name","")).casefold())
    ) + '</div>'

def event_cards(events):
    rows = [e for e in events if e.get("id") and (e.get("name") or e.get("title"))]
    if not rows:
        return '<div class="empty">Nincs jelenleg publikálható, ellenőrzött aktuális vagy jövőbeni program.</div>'
    return '<div class="event-grid">' + "".join(
        f'<article class="event"><div class="date">{esc(e.get("startDate") or e.get("date") or "")}</div>'
        f'<h3>{esc(e.get("name") or e.get("title"))}</h3><p>{esc(e.get("organizer") or "")}'
        + (f'<br>{esc(e.get("venue") or e.get("city") or "")}' if (e.get("venue") or e.get("city")) else "")
        + '</p><div class="event-links">'
        + f'<a href="events/{esc(e.get("id"))}.html">Program részletei →</a>'
        + (f'<a href="{esc(e.get("sourceUrl"))}" target="_blank" rel="noopener external">Eredeti forrás ↗</a>' if e.get("sourceUrl") else "")
        + '</div></article>'
        for e in sorted(rows, key=lambda x: str(x.get("startDate") or x.get("date") or ""))
    ) + '</div>'

registry = read(DATA / "global.json", {"countries":[]})
for country in registry.get("countries", []):
    iso = country["iso2"]
    out = ROOT / "countries" / iso
    out.mkdir(parents=True, exist_ok=True)

    names = country.get("name", {})
    name = names.get("hu") or names.get("en") or iso.upper()
    counts = country.get("counts", {})
    status = country.get("researchStatus", "unresearched")
    ready = status in READY
    orgs, edus, events, state_names = country_data(iso)

    choices = (
        '<a class="choice-card primary-choice" href="#programok"><span>01</span><strong>Programot keresek</strong><small>Aktuális és jövőbeni ellenőrzött programok.</small></a>'
        '<a class="choice-card" href="#oktatas"><span>02</span><strong>Magyar oktatást keresek</strong><small>Iskolák és oktatási lehetőségek.</small></a>'
        '<a class="choice-card" href="#kozossegek"><span>03</span><strong>Közösséget keresek</strong><small>Szervezetek és kapcsolódási pontok.</small></a>'
    )

    if ready:
        regions = entity_sections(orgs, edus, state_names) or '<p class="muted">Ehhez az országhoz nincs publikálható területi rekord.</p>'
        body_sections = (
            f'<section id="teruleti-attekintes" class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Országadatbázis</div><h2>Területi áttekintés</h2><p>Régiók szerint böngészhető, egységes DORAPP rendszerben.</p></div></div>{regions}</div></section>'
            f'<section id="kozossegek" class="section muted"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Közösségek</div><h2>Közösségek és szervezetek.</h2><p>Civil, közösségi és hivatalos intézményi szervezetek, ellenőrzött forrásokkal.</p></div></div>{org_cards(orgs,state_names)}</div></section>'
            f'<section id="oktatas" class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Magyar oktatás</div><h2>Magyar oktatás.</h2><p>Ellenőrzött iskolák, hétvégi iskolák és intézményi programok.</p></div></div>{edu_cards(edus,state_names)}</div></section>'
            f'<section id="programok" class="section muted"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Országos programnaptár</div><h2>Aktuális és jövőbeni programok.</h2><p>Az ország ellenőrzött forrásaiból származó közelgő események.</p></div></div>{event_cards(events)}</div></section>'
        )
    else:
        body_sections = (
            '<section class="section"><div class="wrap"><div class="empty">'
            'Ennek az országnak az adatbázisa még kutatás alatt áll. A már ellenőrzött részadatok nem jelentik a teljes országos lefedettséget.'
            '</div><p><a class="btn" href="../../">Vissza a világtérképhez</a></p></div></section>'
        )

    title = f"Magyar közösségek – {name} | DORAPP"
    canonical = f"{BASE}/countries/{iso}/"
    robots = "index,follow" if ready else "noindex,follow"
    schema = {
        "@context":"https://schema.org",
        "@type":"CollectionPage",
        "name":title,
        "url":canonical,
        "isPartOf":{"@id":BASE+"/#website"},
        "about":{"@type":"Country","name":names.get("en") or name}
    }

    doc = f'''<!doctype html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><link rel="icon" href="../../favicon.svg" type="image/svg+xml"><title>{esc(title)}</title><meta name="description" content="{esc(name)} magyar közösségeinek, szervezeteinek, oktatásának és programjainak forrásalapú DORAPP országoldala."><meta name="robots" content="{robots}"><link rel="canonical" href="{canonical}"><link rel="stylesheet" href="../../styles.css"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False)}</script></head><body><a class="skip" href="#content">Ugrás a tartalomhoz</a><header class="topbar"><div class="wrap navrow"><a class="brand" href="../../"><span class="mark">HU</span><span>DORAPP</span></a><nav><a href="../../">Világ</a><a href="#programok">Programok</a><a href="#oktatas">Oktatás</a><a href="#kozossegek">Közösségek</a></nav></div></header><main id="content"><section class="hero"><div class="wrap"><div class="eyebrow">DORAPP · {iso.upper()}</div><h1>{esc(name)} <span>magyar közösségei</span></h1><p class="lead">{counts.get("organizations",0)} szervezet, {counts.get("education",0)} oktatási rekord és {counts.get("events",0)} program a jelenlegi ellenőrzött adatállapot szerint.</p>{f'<div class="choice-grid country-choice-grid" aria-label="Mit keresel?">{choices}</div>' if ready else ''}<p class="hero-proof"><strong>Forrásalapú országadatbázis.</strong> Kutatási állapot: {esc(status)}.</p></div></section>{body_sections}</main><footer><div class="wrap footer-grid"><div><b>DORAPP</b><p>Forrásalapú magyar diaszpóra-címtár és programnaptár.</p></div><div><a href="../../forrasok.html">Hogyan működik?</a><br><a href="../../adatminoseg.html">Adatminőség és transzparencia</a></div><div><a href="https://www.kozpontiszovetseg.at/kapcsolat" target="_blank" rel="noopener external">Impresszum / kapcsolat ↗</a><br><a href="https://www.kozpontiszovetseg.at/post/gdpr-ai-trust" target="_blank" rel="noopener external">GDPR & AI Trust ↗</a></div></div></footer><script src="../../ui.js?v=20260926-consent-nav" defer></script></body></html>'''
    (out / "index.html").write_text(doc, encoding="utf-8")

print(f"Generated {len(registry.get('countries', []))} country routes")
