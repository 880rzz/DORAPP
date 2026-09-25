#!/usr/bin/env python3
import json,html
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"szervezetek"
DATA=ROOT/"data/organizations.json"
ARTICLES=ROOT/"data/articles.json"
BASE_URL="https://diaszpora.kozpontiszovetseg.at"
OUT.mkdir(exist_ok=True)
db=json.loads(DATA.read_text(encoding="utf-8"))
states={s["id"]:s["name"] for s in db["states"]}
parents={o["id"]:o for o in db["organizations"]}
umbrellas={u["id"]:u for u in db.get("umbrellaOrganizations",[])}
networks={n["id"]:n for n in db.get("regionalNetworks",[])}
article_db=json.loads(ARTICLES.read_text(encoding="utf-8")) if ARTICLES.exists() else {"articles":{}}

def esc(v): return html.escape(str(v or ""),quote=True)

for o in db["organizations"]:
    social=[]
    primary_link = next((o.get(key) for key in ("website","facebook","instagram") if o.get(key)), None)
    for label,key in [("Hivatalos weboldal","website"),("Facebook","facebook"),("Instagram","instagram")]:
        if o.get(key):
            social.append(f'<a class="btn{" primary" if o[key] == primary_link else ""}" href="{esc(o[key])}" target="_blank" rel="noopener external">{label} ↗</a>')
    national_role=o.get("nationalRole") or None
    national_role_html=(f'<a class="membership" href="{esc(national_role.get("sourceUrl"))}" target="_blank" rel="noopener external"><span>Országos szerep</span><strong>{esc(national_role.get("label"))}</strong></a><p>{esc(national_role.get("description"))}</p>') if national_role else ""
    service_locations=o.get("serviceLocations") or []
    service_html="<ul class=\"source-list\">"+"".join(f'<li><strong>{esc(x.get("city"))}</strong> — {esc(x.get("label"))}</li>' for x in service_locations)+"</ul>" if service_locations else ""
    affiliations=o.get("affiliations") or []
    affiliation_html="<div class=\"membership-list\">"+"".join(
        f'<a class="membership" href="../szervezetek/{esc(a.get("organizationId"))}.html"><span>{esc(a.get("label") or "Kapcsolódás")}</span><strong>{esc((parents.get(a.get("organizationId")) or {}).get("name") or a.get("organizationId"))}</strong></a>'
        for a in affiliations
    )+"</div>" if affiliations else ""
    parent=parents.get(o.get("parentOrganizationId")) if o.get("parentOrganizationId") else None
    parent_html=(f'<a class="membership" href="../szervezetek/{esc(parent.get("id"))}.html"><span>Kapcsolódó / szülő szervezet</span><strong>{esc(parent.get("name"))}</strong></a>') if parent else ""
    memberships=o.get("memberships") or []
    membership_html="<div class=\"membership-list\">"+"".join(
        f'<a class="membership" href="{esc((umbrellas.get(m.get("umbrellaId")) or {}).get("url") or m.get("sourceUrl"))}" target="_blank" rel="noopener external"><span>Ernyőszervezeti tagság</span><strong>{esc((umbrellas.get(m.get("umbrellaId")) or {}).get("name") or m.get("umbrellaId"))}</strong></a>'
        for m in memberships
    )+"</div>" if memberships else "<p>Jelenleg nincs igazolt ernyőszervezeti tagság rögzítve.</p>"
    regional=o.get("regionalNetworks") or []
    regional_html="<div class=\"membership-list\">"+"".join(
        f'<a class="membership" href="{esc(r.get("sourceUrl"))}" target="_blank" rel="noopener external"><span>{esc("Regionális központ" if r.get("role")=="hub" else "Regionális együttműködés")}</span><strong>{esc((networks.get(r.get("networkId")) or {}).get("name") or r.get("networkId"))}</strong></a>'
        for r in regional
    )+"</div>" if regional else ""
    articles=(article_db.get("articles") or {}).get(o["id"],[])
    articles_html="<div class=\"article-grid\">"+"".join(
        f'<a class="article-card" href="{esc(a.get("url"))}" target="_blank" rel="noopener external"><span>{esc(a.get("source") or "Cikk")}</span><strong>{esc(a.get("title") or a.get("url"))}</strong><i>Megnyitás ↗</i></a>'
        for a in articles if a.get("url")
    )+"</div>" if articles else "<p>Még gyűjtjük a róluk szóló cikkeket.</p>"
    src=(o.get("eventSources") or [])
    evidence=(o.get("evidenceSources") or [])
    evidence_html="<ul class=\"source-list\">"+"".join(f'<li><a href="{esc(x.get("url"))}" target="_blank" rel="noopener external">{esc(x.get("label") or x.get("url"))}</a></li>' for x in evidence if x.get("url"))+"</ul>" if evidence else "<p>Még nincs külön háttéranyagunk ehhez a közösséghez.</p>"
    src_html="<ul class=\"source-list\">"+"".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener external">{esc(u)}</a></li>' for u in src)+"</ul>" if src else "<p>Ehhez a közösséghez még keresünk olyan saját programoldalt, amit rendszeresen és biztosan lehet frissíteni.</p>"
    schema={"@context":"https://schema.org","@graph":[
      {"@type":"ProfilePage","name":o["name"]+" | Magyar Programok Ausztriában","url":f"{BASE_URL}/szervezetek/{o['id']}.html","inLanguage":"hu-AT","mainEntity":{"@id":"#organization"}},
      {"@type":"Organization","@id":"#organization","name":o["name"],"description":o["intro"],
       "url":primary_link,"sameAs":[x for x in [o.get("website"),o.get("facebook"),o.get("instagram")] if x],
       "areaServed":{"@type":"AdministrativeArea","name":states.get(o["state"],o["state"])},
       "location":{"@type":"Place","address":{"@type":"PostalAddress","addressLocality":o["city"],"addressCountry":"AT"}}}
    ]}
    body=f'''<!doctype html><html lang="hu-AT"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{esc(o["name"])} | Magyar Programok Ausztriában</title><meta name="description" content="{esc(o["intro"])}"><meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large"><link rel="canonical" href="{BASE_URL}/szervezetek/{esc(o["id"])}.html"><link rel="stylesheet" href="../styles.css"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace("</","<\\/")}</script></head><body><header class="topbar"><div class="wrap navrow"><a class="brand" href="../"><span class="mark">AT×HU</span><span>Magyar Programok Ausztriában</span></a><nav><a href="../#terkep">Térkép</a><a href="../#szervezetek">Szervezetek</a><a href="../#naptar">Események</a></nav></div></header><main><section class="hero"><div class="wrap"><div class="eyebrow">{esc(states.get(o["state"],o["state"]))} · {esc(o["city"])} · {esc(o["type"])}</div><h1>{esc(o["name"])}</h1><p class="lead">{esc(o["intro"])}</p><div class="hero-actions">{"".join(social)}</div></div></section><section class="section muted"><div class="wrap trust-grid"><div><h2>Róluk röviden</h2></div><div><p>{esc(o["intro"])}</p><p><strong>Hely:</strong> {esc(o["city"])}, {esc(states.get(o["state"],o["state"]))}<br><strong>Típus:</strong> {esc(o["type"])}</p></div></div></section>{("<section class=\"section\"><div class=\"wrap trust-grid\"><div><h2>Országos szerep</h2></div><div>"+national_role_html+"</div></div></section>") if national_role_html else ""}{("<section class=\"section\"><div class=\"wrap trust-grid\"><div><h2>Hol találkozhatsz velük?</h2></div><div>"+service_html+"</div></div></section>") if service_html else ""}{("<section class=\"section\"><div class=\"wrap trust-grid\"><div><h2>Kapcsolódó szervezet</h2></div><div>"+parent_html+"</div></div></section>") if parent_html else ""}{("<section class=\"section\"><div class=\"wrap trust-grid\"><div><h2>Kapcsolódó szervezetek</h2></div><div>"+affiliation_html+"</div></div></section>") if affiliation_html else ""}<section class="section"><div class="wrap trust-grid"><div><h2>Ernyőszervezeti kapcsolódás</h2></div><div>{membership_html}</div></div></section>{("<section class=\"section muted\"><div class=\"wrap trust-grid\"><div><h2>Regionális együttműködés</h2></div><div>"+regional_html+"</div></div></section>") if regional_html else ""}<section class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">A következő alkalmak</div><h2>Programok</h2></div></div><div id="relatedEvents" class="event-grid"></div></div></section><section class="section muted"><div class="wrap trust-grid"><div><h2>Hol érdemes még megnézni?</h2></div><div>{src_html}</div></div></section><section class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Cikkek és háttéranyagok</div><h2>Róluk írták.</h2></div></div>{articles_html}</div></section><section class="section muted"><div class="wrap trust-grid"><div><h2>Róluk máshol</h2></div><div>{evidence_html}</div></div></section></main><script>const ORG_ID={json.dumps(o["id"])};const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[c]));const fmt=s=>{{if(!s)return"";const d=new Date(s);return Number.isNaN(d)?s:new Intl.DateTimeFormat("hu-AT",{{dateStyle:"long",timeStyle:String(s).includes("T")?"short":undefined}}).format(d)}};const routes=a=>{{if(!a)return"";const q=encodeURIComponent(a);return '<a href="https://www.google.com/maps/dir/?api=1&destination='+q+'" target="_blank" rel="noopener external">Google Maps útvonal ↗</a><a href="https://maps.apple.com/?daddr='+q+'" target="_blank" rel="noopener external">Apple Maps ↗</a>'}};fetch("../data/events.json",{{cache:"no-store"}}).then(r=>r.json()).then(d=>{{const now=new Date(),x=(d.events||[]).filter(e=>e.organizationId===ORG_ID&&(!e.endDate||new Date(e.endDate)>=now)).sort((a,b)=>String(a.startDate).localeCompare(String(b.startDate)));document.querySelector("#relatedEvents").innerHTML=x.length?x.map(e=>'<article class="event"><div class="date">'+esc(fmt(e.startDate))+'</div><h3>'+esc(e.name)+'</h3><p>'+esc([e.venue,e.address||e.city].filter(Boolean).join(" · "))+'</p><div class="event-links">'+(e.sourceUrl?'<a href="'+esc(e.sourceUrl)+'" target="_blank" rel="noopener external">Forrás ↗</a>':'')+routes(e.address)+'</div></article>').join(""):'<div class="empty">Most nincs olyan közelgő program, amit biztos forrásból meg tudunk mutatni.</div>'}});</script></body></html>'''
    (OUT/f'{o["id"]}.html').write_text(body,encoding="utf-8")
print(f"generated={len(db['organizations'])}")
