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
    history=o.get("history") or {}
    milestones=history.get("milestones") or []
    milestone_html="<ul class=\"source-list\">"+"".join(
        f'<li><strong>{esc(m.get("date") or m.get("year") or "")}</strong>{" — " if (m.get("date") or m.get("year")) else ""}{esc(m.get("title") or "")}{(": "+esc(m.get("description"))) if m.get("description") else ""}{(" <a href=\"" + esc(m.get("sourceUrl")) + "\" target=\"_blank\" rel=\"noopener external\">Forrás ↗</a>") if m.get("sourceUrl") else ""}</li>'
        for m in milestones
    )+"</ul>" if milestones else ""
    history_parts=[]
    if history.get("summary"): history_parts.append(f'<p>{esc(history.get("summary"))}</p>')
    if milestone_html: history_parts.append(milestone_html)
    history_html="".join(history_parts)
    activities=o.get("activities") or []
    activities_html="<ul class=\"source-list\">"+"".join(f'<li>{esc(x)}</li>' for x in activities)+"</ul>" if activities else ""
    target_groups=o.get("targetGroups") or []
    target_html="<ul class=\"source-list\">"+"".join(f'<li>{esc(x)}</li>' for x in target_groups)+"</ul>" if target_groups else ""
    languages=o.get("languages") or []
    contact_bits=[]
    if o.get("email"): contact_bits.append(f'<a href="mailto:{esc(o.get("email"))}">{esc(o.get("email"))}</a>')
    if o.get("phone"): contact_bits.append(f'<a href="tel:{esc(o.get("phone"))}">{esc(o.get("phone"))}</a>')
    if languages: contact_bits.append("Nyelv: "+", ".join(esc(x) for x in languages))
    if o.get("profileVerifiedAt"): contact_bits.append("Profiladatok ellenőrizve: "+esc(o.get("profileVerifiedAt")))
    contact_html="<p>"+"<br>".join(contact_bits)+"</p>" if contact_bits else ""
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
    page_url=f"{BASE_URL}/szervezetek/{o['id']}.html"
    publisher={"@type":"Organization","@id":BASE_URL+"/#publisher","name":"Ausztriai Magyar Egyesületek és Szervezetek Központi Szövetsége","url":"https://www.kozpontiszovetseg.at/","identifier":{"@type":"PropertyValue","propertyID":"ZVR","value":"079797621"}}
    org_schema={"@type":"Organization","@id":page_url+"#organization","name":o["name"],"description":o["intro"],
       "url":primary_link or page_url,"sameAs":[x for x in [o.get("website"),o.get("facebook"),o.get("instagram")] if x],
       **({"foundingDate":o.get("founded")} if o.get("founded") else {}),
       **({"email":o.get("email")} if o.get("email") else {}),
       **({"telephone":o.get("phone")} if o.get("phone") else {}),
       "areaServed":{"@type":"AdministrativeArea","name":states.get(o["state"],o["state"])},
       "location":{"@type":"Place","address":{"@type":"PostalAddress","addressLocality":o["city"],"addressCountry":"AT"}}}
    if memberships:
        org_schema["memberOf"]=[{"@type":"Organization","name":(umbrellas.get(m.get("umbrellaId")) or {}).get("name") or m.get("umbrellaId"),"url":(umbrellas.get(m.get("umbrellaId")) or {}).get("url") or m.get("sourceUrl")} for m in memberships]
    if parent:
        org_schema["parentOrganization"]={"@type":"Organization","name":parent.get("name"),"url":f"{BASE_URL}/szervezetek/{parent.get('id')}.html"}
    schema={"@context":"https://schema.org","@graph":[
      {"@type":"ProfilePage","@id":page_url+"#page","name":o["name"]+" | Magyar Programok Ausztriában","url":page_url,"inLanguage":"hu-AT","mainEntity":{"@id":page_url+"#organization"},"isPartOf":{"@id":BASE_URL+"/#website"},"publisher":{"@id":BASE_URL+"/#publisher"}},
      org_schema,
      publisher,
      {"@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"Magyar Programok Ausztriában","item":BASE_URL+"/"},
        {"@type":"ListItem","position":2,"name":"Szervezetek","item":BASE_URL+"/#szervezetek"},
        {"@type":"ListItem","position":3,"name":o["name"],"item":page_url}
      ]}
    ]}
    body=f'''<!doctype html><html lang="hu-AT"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{esc(o["name"])} | Magyar Programok Ausztriában</title><meta name="description" content="{esc(o["intro"])}"><meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large"><link rel="canonical" href="{BASE_URL}/szervezetek/{esc(o["id"])}.html"><meta property="og:type" content="profile"><meta property="og:title" content="{esc(o["name"])}"><meta property="og:description" content="{esc(o["intro"])}"><meta property="og:url" content="{BASE_URL}/szervezetek/{esc(o["id"])}.html"><meta name="twitter:card" content="summary"><link rel="stylesheet" href="../styles.css"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace("</","<\\/")}</script></head><body><header class="topbar"><div class="wrap navrow"><a class="brand" href="../"><span class="mark">AT×HU</span><span>Magyar Programok Ausztriában</span></a><nav><a href="../#terkep">Térkép</a><a href="../#szervezetek">Szervezetek</a><a href="../#naptar">Események</a></nav></div></header><main><section class="hero"><div class="wrap"><div class="eyebrow">{esc(states.get(o["state"],o["state"]))} · {esc(o["city"])} · {esc(o["type"])}</div><h1>{esc(o["name"])}</h1><p class="lead">{esc(o["intro"])}</p><div class="hero-actions">{"".join(social)}</div></div></section><section class="section muted"><div class="wrap trust-grid"><div><h2>Róluk röviden</h2></div><div><p>{esc(o["intro"])}</p><p><strong>Hely:</strong> {esc(o["city"])}, {esc(states.get(o["state"],o["state"]))}<br><strong>Típus:</strong> {esc(o["type"])}</p></div></div></section>{("<section class=\"section\"><div class=\"wrap trust-grid\"><div><h2>Történet</h2></div><div>"+history_html+"</div></div></section>") if history_html else ""}{("<section class=\"section muted\"><div class=\"wrap trust-grid\"><div><h2>Mit csinálnak?</h2></div><div>"+activities_html+"</div></div></section>") if activities_html else ""}{("<section class=\"section\"><div class=\"wrap trust-grid\"><div><h2>Kiknek szól?</h2></div><div>"+target_html+"</div></div></section>") if target_html else ""}{("<section class=\"section muted\"><div class=\"wrap trust-grid\"><div><h2>Kapcsolat és profiladatok</h2></div><div>"+contact_html+"</div></div></section>") if contact_html else ""}{("<section class=\"section\"><div class=\"wrap trust-grid\"><div><h2>Országos szerep</h2></div><div>"+national_role_html+"</div></div></section>") if national_role_html else ""}{("<section class=\"section\"><div class=\"wrap trust-grid\"><div><h2>Hol találkozhatsz velük?</h2></div><div>"+service_html+"</div></div></section>") if service_html else ""}{("<section class=\"section\"><div class=\"wrap trust-grid\"><div><h2>Kapcsolódó szervezet</h2></div><div>"+parent_html+"</div></div></section>") if parent_html else ""}{("<section class=\"section\"><div class=\"wrap trust-grid\"><div><h2>Kapcsolódó szervezetek</h2></div><div>"+affiliation_html+"</div></div></section>") if affiliation_html else ""}<section class="section"><div class="wrap trust-grid"><div><h2>Ernyőszervezeti kapcsolódás</h2></div><div>{membership_html}</div></div></section>{("<section class=\"section muted\"><div class=\"wrap trust-grid\"><div><h2>Regionális együttműködés</h2></div><div>"+regional_html+"</div></div></section>") if regional_html else ""}<section class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">A következő alkalmak</div><h2>Programok</h2></div></div><div id="relatedEvents" class="event-grid"></div></div></section><section class="section muted"><div class="wrap trust-grid"><div><h2>Hol érdemes még megnézni?</h2></div><div>{src_html}</div></div></section><section class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Cikkek és háttéranyagok</div><h2>Róluk írták.</h2></div></div>{articles_html}</div></section><section class="section muted"><div class="wrap trust-grid"><div><h2>Róluk máshol</h2></div><div>{evidence_html}</div></div></section></main><footer><div class="wrap footer-grid"><div><b>Magyar Programok Ausztriában</b><p>Forrásalapú közösségi címtár és programnaptár.</p></div><div><a href="../forrasok.html">Hogyan működik?</a><br><a href="https://www.kozpontiszovetseg.at/kapcsolat" target="_blank" rel="noopener external">Impresszum / kapcsolat ↗</a></div><div><a href="https://www.kozpontiszovetseg.at/post/gdpr-ai-trust" target="_blank" rel="noopener external">GDPR & AI Trust ↗</a><br>Fejlesztette a <a href="https://rolunk.at/aktualis/a-fiataloknak-ma-mar-bizonyitek-kell-egy-becsi-kreativ-kozosseg-uj-generaciot-epit/" target="_blank" rel="noopener external">Be Smart Kids Club csapata</a><br><a href="https://business.vipach.at" target="_blank" rel="noopener external">business.vipach.at</a></div></div></footer><script>const ORG_ID={json.dumps(o["id"])};const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[c]));const fmt=s=>{{if(!s)return"";const d=new Date(s);return Number.isNaN(d)?s:new Intl.DateTimeFormat("hu-AT",{{dateStyle:"long",timeStyle:String(s).includes("T")?"short":undefined}}).format(d)}};const routes=a=>{{if(!a)return"";const q=encodeURIComponent(a);return '<a href="https://www.google.com/maps/dir/?api=1&destination='+q+'" target="_blank" rel="noopener external">Google Maps útvonal ↗</a><a href="https://maps.apple.com/?daddr='+q+'" target="_blank" rel="noopener external">Apple Maps ↗</a>'}};fetch("../data/events.json",{{cache:"no-store"}}).then(r=>r.json()).then(d=>{{const now=new Date(),x=(d.events||[]).filter(e=>e.organizationId===ORG_ID&&(!e.endDate||new Date(e.endDate)>=now)).sort((a,b)=>String(a.startDate).localeCompare(String(b.startDate)));document.querySelector("#relatedEvents").innerHTML=x.length?x.map(e=>'<article class="event"><div class="date">'+esc(fmt(e.startDate))+(e.endDate?' – '+esc(fmt(e.endDate)):'')+'</div><h3>'+esc(e.name)+'</h3><p>'+esc([e.venue,e.address||e.city].filter(Boolean).join(" · "))+'</p>'+(e.description?'<p>'+esc(e.description)+'</p>':'')+((e.performers||[]).length?'<p><strong>Fellépők / közreműködők:</strong> '+esc(e.performers.join(", "))+'</p>':'')+(e.audience?'<p><strong>Célcsoport:</strong> '+esc(e.audience)+'</p>':'')+(e.price!=null?'<p><strong>Ár:</strong> '+esc(e.price+' '+(e.priceCurrency||''))+'</p>':'')+'<div class="event-links"><a href="../esemenyek/'+encodeURIComponent(e.id)+'.html">DORAPP programoldal →</a>'+(e.registrationUrl?'<a href="'+esc(e.registrationUrl)+'" target="_blank" rel="noopener external">Regisztráció / jegy ↗</a>':'')+(e.sourceUrl?'<a href="'+esc(e.sourceUrl)+'" target="_blank" rel="noopener external">Forrás ↗</a>':'')+routes(e.address)+'</div></article>').join(""):'<div class="empty">Most nincs olyan közelgő program, amit biztos forrásból meg tudunk mutatni.</div>'}});</script></body></html>'''
    (OUT/f'{o["id"]}.html').write_text(body,encoding="utf-8")
print(f"generated={len(db['organizations'])}")
