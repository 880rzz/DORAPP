#!/usr/bin/env python3
import json,html
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"oktatas"
DATA=ROOT/"data/education.json"
ORG=ROOT/"data/organizations.json"
HEALTH=ROOT/"data/education-site-health.json"
BASE_URL="https://diaszpora.kozpontiszovetseg.at"
OUT.mkdir(exist_ok=True)

ed=json.loads(DATA.read_text(encoding="utf-8"))
org=json.loads(ORG.read_text(encoding="utf-8"))
health=json.loads(HEALTH.read_text(encoding="utf-8")) if HEALTH.exists() else {"sites":[]}
states={s["id"]:s["name"] for s in org.get("states",[])}
health_by_id={x["id"]:x for x in health.get("sites",[])}
EDU_UPDATED=str(ed.get("updated") or "")[:10]

LEVELS={
 "nursery":"Bölcsőde / 0–3 év",
 "kindergarten":"Óvoda / 3–6 év",
 "primary":"Népiskola",
 "secondary":"Középiskola",
 "tertiary":"Felsőoktatás",
 "adult":"Felnőttoktatás"
}

def esc(v): return html.escape(str(v or ""),quote=True)

def audit_text(h):
    if not h:return "A weboldal automatikus ellenőrzéséről még nincs adat."
    s=h.get("status")
    if s=="relevant-content-found":return "A legutóbbi webaudit releváns magyar vagy többnyelvű tartalmat talált a saját oldalon."
    if s=="reachable-no-relevant-keywords":return "A weboldal elérhető, de a legutóbbi audit nem talált rajta külön magyar tartalmat."
    if s=="no-website":return "Ehhez a helyszínhez jelenleg nincs külön, igazolt saját weboldalunk."
    if s=="error":return "A weboldalt az utolsó automatikus ellenőrzéskor technikai okból nem sikerült beolvasni."
    return "A weboldal ellenőrzése folyamatban van."

for x in ed.get("institutions",[]):
    h=health_by_id.get(x["id"])
    levels=", ".join(LEVELS.get(v,v) for v in x.get("level",[]))
    links=[]
    if x.get("website"):links.append(f'<a class="btn primary" href="{esc(x["website"])}" target="_blank" rel="noopener external">Intézmény oldala ↗</a>')
    if x.get("sourceUrl"):links.append(f'<a class="btn" href="{esc(x["sourceUrl"])}" target="_blank" rel="noopener external">Igazoló forrás ↗</a>')
    matches=[]
    if h:
        for group,vals in (h.get("matches") or {}).items():
            matches.extend(vals)
    matches_html=", ".join(sorted(set(matches)))
    page_url=f"{BASE_URL}/oktatas/{x['id']}.html"
    publisher={"@type":"Organization","@id":BASE_URL+"/#publisher","name":"Ausztriai Magyar Egyesületek és Szervezetek Központi Szövetsége","url":"https://www.kozpontiszovetseg.at/","identifier":{"@type":"PropertyValue","propertyID":"ZVR","value":"079797621"}}
    edu_schema={"@type":"EducationalOrganization","@id":page_url+"#education","name":x["name"],"description":x["summary"],
       "url":x.get("website") or page_url,
       **({"sameAs":[x.get("website")]} if x.get("website") else {}),
       "areaServed":{"@type":"AdministrativeArea","name":states.get(x["state"],x["state"])},
       "location":{"@type":"Place","address":{"@type":"PostalAddress","addressLocality":x["city"],"addressCountry":"AT"}},
       **({"dateModified":EDU_UPDATED} if EDU_UPDATED else {})}
    schema={"@context":"https://schema.org","@graph":[
      {"@type":"ProfilePage","@id":page_url+"#page","name":x["name"]+" | Magyar oktatás Ausztriában","url":page_url,"inLanguage":"hu-AT","mainEntity":{"@id":page_url+"#education"},"isPartOf":{"@id":BASE_URL+"/#website"},"publisher":{"@id":BASE_URL+"/#publisher"},**({"dateModified":EDU_UPDATED} if EDU_UPDATED else {})},
      edu_schema,publisher,
      {"@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"Magyar Programok Ausztriában","item":BASE_URL+"/"},
        {"@type":"ListItem","position":2,"name":"Magyar oktatás","item":BASE_URL+"/#oktatas"},
        {"@type":"ListItem","position":3,"name":x["name"],"item":page_url}
      ]}
    ]}
    body=f'''<!doctype html><html lang="hu-AT"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{esc(x["name"])} | Magyar oktatás Ausztriában</title><meta name="description" content="{esc(x["summary"])}"><meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large"><link rel="canonical" href="{BASE_URL}/oktatas/{esc(x["id"])}.html"><meta property="og:type" content="website"><meta property="og:title" content="{esc(x["name"])}"><meta property="og:description" content="{esc(x["summary"])}"><meta property="og:url" content="{BASE_URL}/oktatas/{esc(x["id"])}.html"><meta name="twitter:card" content="summary"><link rel="stylesheet" href="../styles.css"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace("</","<\\/")}</script></head><body><header class="topbar"><div class="wrap navrow"><a class="brand" href="../"><span class="mark">AT×HU</span><span>Magyar Programok Ausztriában</span></a><nav><a href="../#terkep">Térkép</a><a href="../#szervezetek">Közösségek</a><a href="../#oktatas">Oktatás</a><a href="../#naptar">Programok</a></nav></div></header><main><section class="hero"><div class="wrap"><div class="eyebrow">{esc(states.get(x["state"],x["state"]))} · {esc(x["city"])} · {esc(x["type"])}</div><h1>{esc(x["name"])}</h1><p class="lead">{esc(x["summary"])}</p><div class="hero-actions">{"".join(links)}</div></div></section><section class="section muted"><div class="wrap trust-grid"><div><h2>Oktatási adatok</h2></div><div><p><strong>Hely:</strong> {esc(x["city"])}, {esc(states.get(x["state"],x["state"]))}<br><strong>Szint:</strong> {esc(levels)}<br><strong>Típus:</strong> {esc(x["type"])}{f'<br><strong>Utoljára igazolt tanév:</strong> {esc(x.get("verifiedPeriod"))}' if x.get("verifiedPeriod") else ""}</p></div></div></section><section class="section"><div class="wrap trust-grid"><div><h2>Weboldal-ellenőrzés</h2></div><div><p>{esc(audit_text(h))}</p>{f'<p><strong>Ellenőrzött oldalak:</strong> {h.get("pagesChecked",0)}</p>' if h else ''}{f'<p><strong>Talált kifejezések:</strong> {esc(matches_html)}</p>' if matches_html else ''}</div></div></section><section class="section muted"><div class="wrap trust-grid"><div><h2>Forrás</h2></div><div><p>Az oktatási helyet csak ellenőrizhető intézményi vagy szerkesztőségi forrás alapján tartjuk nyilván.</p>{f'<p><a href="{esc(x.get("sourceUrl"))}" target="_blank" rel="noopener external">Forrás megnyitása ↗</a></p>' if x.get("sourceUrl") else ''}</div></div></section></main><footer><div class="wrap footer-grid"><div><b>Magyar Programok Ausztriában</b><p>Magyar oktatási lehetőségek, közösségek és programok egész Ausztriában.</p></div><div><a href="../#oktatas">Vissza az oktatási keresőhöz</a></div><div><p>Ha egy intézmény kínálata megváltozik, mindig a legfrissebb hivatalos közlés az irányadó.</p><a href="https://www.kozpontiszovetseg.at/kapcsolat" target="_blank" rel="noopener external">Impresszum / kapcsolat ↗</a><br><a href="https://www.kozpontiszovetseg.at/post/gdpr-ai-trust" target="_blank" rel="noopener external">GDPR & AI Trust ↗</a><br>Fejlesztette a <a href="https://rolunk.at/aktualis/a-fiataloknak-ma-mar-bizonyitek-kell-egy-becsi-kreativ-kozosseg-uj-generaciot-epit/" target="_blank" rel="noopener external">Be Smart Kids Club csapata</a><br><a href="https://business.vipach.at" target="_blank" rel="noopener external">business.vipach.at</a></div></div></footer></body></html>'''
    (OUT/f'{x["id"]}.html').write_text(body,encoding="utf-8")

print(f"education_profiles={len(ed.get('institutions',[]))}")
