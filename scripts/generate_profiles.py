#!/usr/bin/env python3
import json,html
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"szervezetek"
DATA=ROOT/"data/organizations.json"
OUT.mkdir(exist_ok=True)
db=json.loads(DATA.read_text(encoding="utf-8"))
states={s["id"]:s["name"] for s in db["states"]}

def esc(v): return html.escape(str(v or ""),quote=True)

for o in db["organizations"]:
    social=[]
    for label,key in [("Hivatalos weboldal","website"),("Facebook","facebook"),("Instagram","instagram")]:
        if o.get(key):
            social.append(f'<a class="btn{" primary" if key=="website" else ""}" href="{esc(o[key])}" target="_blank" rel="noopener external">{label} ↗</a>')
    src=(o.get("eventSources") or [])
    src_html="<ul class=\"source-list\">"+"".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener external">{esc(u)}</a></li>' for u in src)+"</ul>" if src else "<p>Ehhez a közösséghez még keresünk olyan saját programoldalt, amit rendszeresen és biztosan lehet frissíteni.</p>"
    schema={"@context":"https://schema.org","@graph":[
      {"@type":"ProfilePage","name":o["name"]+" | Magyar Programok Ausztriában","inLanguage":"hu-AT","mainEntity":{"@id":"#organization"}},
      {"@type":"Organization","@id":"#organization","name":o["name"],"description":o["intro"],
       "url":o.get("website"),"sameAs":[x for x in [o.get("website"),o.get("facebook"),o.get("instagram")] if x],
       "areaServed":{"@type":"AdministrativeArea","name":states.get(o["state"],o["state"])},
       "location":{"@type":"Place","address":{"@type":"PostalAddress","addressLocality":o["city"],"addressCountry":"AT"}}}
    ]}
    body=f'''<!doctype html><html lang="hu-AT"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{esc(o["name"])} | Magyar Programok Ausztriában</title><meta name="description" content="{esc(o["intro"])}"><meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large"><link rel="stylesheet" href="../styles.css"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace("</","<\\/")}</script></head><body><header class="topbar"><div class="wrap navrow"><a class="brand" href="../"><span class="mark">AT×HU</span><span>Magyar Programok Ausztriában</span></a><nav><a href="../#terkep">Térkép</a><a href="../#szervezetek">Szervezetek</a><a href="../#naptar">Események</a></nav></div></header><main><section class="hero"><div class="wrap"><div class="eyebrow">{esc(states.get(o["state"],o["state"]))} · {esc(o["city"])} · {esc(o["type"])}</div><h1>{esc(o["name"])}</h1><p class="lead">{esc(o["intro"])}</p><div class="hero-actions">{"".join(social)}</div></div></section><section class="section muted"><div class="wrap trust-grid"><div><h2>Róluk röviden</h2></div><div><p>{esc(o["intro"])}</p><p><strong>Hely:</strong> {esc(o["city"])}, {esc(states.get(o["state"],o["state"]))}<br><strong>Típus:</strong> {esc(o["type"])}</p></div></div></section><section class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">A következő alkalmak</div><h2>Programok</h2></div></div><div id="relatedEvents" class="event-grid"></div></div></section><section class="section muted"><div class="wrap trust-grid"><div><h2>Hol érdemes még megnézni?</h2></div><div>{src_html}</div></div></section></main><script>const ORG_ID={json.dumps(o["id"])};const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[c]));const fmt=s=>{{if(!s)return"";const d=new Date(s);return Number.isNaN(d)?s:new Intl.DateTimeFormat("hu-AT",{{dateStyle:"long",timeStyle:String(s).includes("T")?"short":undefined}}).format(d)}};const routes=a=>{{if(!a)return"";const q=encodeURIComponent(a);return '<a href="https://www.google.com/maps/dir/?api=1&destination='+q+'" target="_blank" rel="noopener external">Google Maps útvonal ↗</a><a href="https://maps.apple.com/?daddr='+q+'" target="_blank" rel="noopener external">Apple Maps ↗</a>'}};fetch("../data/events.json",{{cache:"no-store"}}).then(r=>r.json()).then(d=>{{const now=new Date(),x=(d.events||[]).filter(e=>e.organizationId===ORG_ID&&(!e.endDate||new Date(e.endDate)>=now)).sort((a,b)=>String(a.startDate).localeCompare(String(b.startDate)));document.querySelector("#relatedEvents").innerHTML=x.length?x.map(e=>'<article class="event"><div class="date">'+esc(fmt(e.startDate))+'</div><h3>'+esc(e.name)+'</h3><p>'+esc([e.venue,e.address||e.city].filter(Boolean).join(" · "))+'</p><div class="event-links">'+(e.sourceUrl?'<a href="'+esc(e.sourceUrl)+'" target="_blank" rel="noopener external">Forrás ↗</a>':'')+routes(e.address)+'</div></article>').join(""):'<div class="empty">Most nincs olyan közelgő program, amit biztos forrásból meg tudunk mutatni.</div>'}});</script></body></html>'''
    (OUT/f'{o["id"]}.html').write_text(body,encoding="utf-8")
print(f"generated={len(db['organizations'])}")
