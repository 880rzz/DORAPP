#!/usr/bin/env python3
import json, html
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
BASE="https://diaszpora.kozpontiszovetseg.at"

def read(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return d

def esc(v):
    return html.escape(str(v or ""),quote=True)

def links(items):
    return "".join(items)

def source_list(items, empty="Nincs külön forrás rögzítve."):
    rows=[]
    for x in items or []:
        if isinstance(x,str):
            url=x; label=x; note=""
        else:
            url=x.get("url"); label=x.get("label") or x.get("platform") or url
            extra=[]
            if x.get("platform"): extra.append(str(x.get("platform")))
            if x.get("ownership") in {"parent","related"}: extra.append("kapcsolódó szervezeti csatorna")
            if "ingestEvents" in x: extra.append("automatikus import" if x.get("ingestEvents") else "ellenőrzött hivatkozás")
            note=(" · "+" · ".join(extra)) if extra else ""
        if url: rows.append(f'<li><a href="{esc(url)}" target="_blank" rel="noopener external">{esc(label)} ↗</a>{esc(note)}</li>')
    return '<ul class="source-list">'+"".join(rows)+'</ul>' if rows else f'<p>{esc(empty)}</p>'

def text_list(items):
    vals=[str(x) for x in (items or []) if x]
    return '<ul class="source-list">'+"".join(f'<li>{esc(x)}</li>' for x in vals)+'</ul>' if vals else ""

def event_future(e):
    raw=e.get("endDate") or e.get("startDate") or e.get("date")
    if not raw:return True
    try:
        d=datetime.fromisoformat(str(raw).replace("Z","+00:00"))
        if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
        return d >= datetime.now(timezone.utc)
    except Exception:
        return True

def main():
    g=read(DATA/"global.json",{"countries":[]})
    generated=0
    for c in g.get("countries",[]):
        iso=c["iso2"]
        country_name=c.get("name",{}).get("hu") or c.get("name",{}).get("en") or iso.upper()
        base=DATA/"countries"/iso
        org_doc=read(base/"organizations.json",{"organizations":[]})
        events_doc=read(base/"events.json",{"events":[]})
        article_doc=read(base/"articles.json",{"articles":{}})
        orgs=org_doc.get("organizations",org_doc.get("items",[]))
        events=events_doc.get("events",events_doc.get("items",[]))
        by_id={o.get("id"):o for o in orgs if o.get("id")}

        for o in orgs:
            eid=o.get("id")
            if not eid or o.get("entityClass")=="activity":
                continue
            out=ROOT/"countries"/iso/"organizations"
            out.mkdir(parents=True,exist_ok=True)
            url=f"{BASE}/countries/{iso}/organizations/{eid}.html"
            title=f"{o.get('name')} | DORAPP"
            intro=o.get("intro") or o.get("summary") or f"Ellenőrzött magyar diaszpóra-szervezeti profil {country_name} területén."
            desc=intro[:280]

            socials=[]
            for label,key in (("Weboldal","website"),("Facebook","facebook"),("Instagram","instagram"),("YouTube","youtube"),("LinkedIn","linkedin")):
                if o.get(key): socials.append((label,o.get(key)))
            for ch in o.get("publicChannels") or []:
                if ch.get("url") and not any(u==ch.get("url") for _,u in socials):
                    socials.append((ch.get("label") or ch.get("platform") or "Közösségi oldal",ch.get("url")))

            hero_actions="".join(f'<a class="btn{" primary" if i==0 else ""}" href="{esc(u)}" target="_blank" rel="noopener external">{esc(l)} ↗</a>' for i,(l,u) in enumerate(socials[:6]))
            contact=[]
            if o.get("email"):contact.append(f'<a href="mailto:{esc(o.get("email"))}">{esc(o.get("email"))}</a>')
            if o.get("phone"):contact.append(f'<a href="tel:{esc(o.get("phone"))}">{esc(o.get("phone"))}</a>')
            if o.get("address"):contact.append("Cím: "+esc(o.get("address")))
            if o.get("contactName"):contact.append("Kapcsolattartó: "+esc(o.get("contactName")))
            if o.get("contactUrl"):contact.append(f'<a href="{esc(o.get("contactUrl"))}" target="_blank" rel="noopener external">Kapcsolati oldal ↗</a>')
            if o.get("profileVerifiedAt"):contact.append("Profiladatok ellenőrizve: "+esc(o.get("profileVerifiedAt")))
            contact_html="<p>"+"<br>".join(contact)+"</p>" if contact else "<p>Nincs külön nyilvános kapcsolati adat rögzítve.</p>"

            history=o.get("history") or {}
            history_parts=[]
            if history.get("summary"):history_parts.append(f'<p>{esc(history.get("summary"))}</p>')
            milestones=history.get("milestones") or []
            if milestones:
                history_parts.append('<ul class="source-list">'+"".join(
                    f'<li><strong>{esc(m.get("date") or m.get("year") or "")}</strong>{(" — "+esc(m.get("title"))) if m.get("title") else ""}{(": "+esc(m.get("description"))) if m.get("description") else ""}{(f""" <a href="{esc(m.get("sourceUrl"))}" target="_blank" rel="noopener external">Forrás ↗</a>""" if m.get("sourceUrl") else "")}</li>'
                    for m in milestones
                )+'</ul>')
            if not history_parts and o.get("founded"):history_parts.append(f'<p><strong>Alapítás:</strong> {esc(o.get("founded"))}</p>')
            history_html="".join(history_parts)

            service=o.get("serviceLocations") or []
            service_html='<ul class="source-list">'+"".join(f'<li><strong>{esc(x.get("city") or x.get("label"))}</strong>{(" — "+esc(x.get("address") or x.get("label"))) if (x.get("address") or x.get("label")) else ""}</li>' for x in service)+'</ul>' if service else ""

            relationship_cards=[]
            parent=by_id.get(o.get("parentOrganizationId"))
            if parent:
                relationship_cards.append(f'<a class="membership" href="{esc(parent.get("id"))}.html"><span>Szülő / kapcsolódó szervezet</span><strong>{esc(parent.get("name"))}</strong></a>')
            for a in o.get("affiliations") or []:
                rid=a.get("organizationId")
                related=by_id.get(rid) if rid else None
                label=a.get("label") or a.get("relationship") or "Kapcsolódás"
                if related:
                    relationship_cards.append(f'<a class="membership" href="{esc(related.get("id"))}.html"><span>{esc(label)}</span><strong>{esc(related.get("name"))}</strong></a>')
                elif a.get("organization"):
                    relationship_cards.append(f'<div class="membership"><span>{esc(label)}</span><strong>{esc(a.get("organization"))}</strong></div>')
            for m in o.get("memberships") or []:
                label=m.get("label") or "Ernyőszervezeti tagság"
                name=m.get("name") or m.get("umbrellaName") or m.get("umbrellaId")
                u=m.get("url") or m.get("sourceUrl")
                if u:
                    relationship_cards.append(f'<a class="membership" href="{esc(u)}" target="_blank" rel="noopener external"><span>{esc(label)}</span><strong>{esc(name)}</strong></a>')
                elif name:
                    relationship_cards.append(f'<div class="membership"><span>{esc(label)}</span><strong>{esc(name)}</strong></div>')
            for r in o.get("regionalNetworks") or []:
                name=r.get("name") or r.get("networkName") or r.get("networkId")
                label="Regionális központ" if r.get("role")=="hub" else "Regionális együttműködés"
                if r.get("sourceUrl"):
                    relationship_cards.append(f'<a class="membership" href="{esc(r.get("sourceUrl"))}" target="_blank" rel="noopener external"><span>{label}</span><strong>{esc(name)}</strong></a>')
                elif name:
                    relationship_cards.append(f'<div class="membership"><span>{label}</span><strong>{esc(name)}</strong></div>')
            relation_html='<div class="membership-list">'+"".join(relationship_cards)+'</div>' if relationship_cards else '<p>Jelenleg nincs külön igazolt szervezeti kapcsolat rögzítve.</p>'

            related=[e for e in events if event_future(e) and (e.get("organizerId")==eid or e.get("organizationId")==eid)]
            related.sort(key=lambda x:str(x.get("startDate") or x.get("date") or ""))
            events_html='<div class="event-grid">'+"".join(
                f'<article class="event"><div class="date">{esc(e.get("startDate") or e.get("date") or "")}</div><h3>{esc(e.get("name") or e.get("title"))}</h3><p>{esc(" · ".join(str(x) for x in [e.get("city"),e.get("venue")] if x))}</p><div class="event-links"><a href="../events/{esc(e.get("id"))}.html">DORAPP programoldal →</a>{(f"""<a href="{esc(e.get("sourceUrl"))}" target="_blank" rel="noopener external">Forrás ↗</a>""" if e.get("sourceUrl") else "")}</div></article>'
                for e in related
            )+'</div>' if related else '<div class="empty">Most nincs olyan közelgő program, amit biztos forrásból ehhez a szervezethez tudunk kötni.</div>'

            articles=(article_doc.get("articles") or {}).get(eid,[])
            article_html='<div class="article-grid">'+"".join(
                f'<a class="article-card" href="{esc(a.get("url"))}" target="_blank" rel="noopener external"><span>{esc(a.get("source") or "Cikk")}</span><strong>{esc(a.get("title") or a.get("url"))}</strong><i>Megnyitás ↗</i></a>'
                for a in articles if a.get("url")
            )+'</div>' if articles else '<p>Még nincs külön sajtó- vagy háttéranyag rögzítve.</p>'

            activities=text_list(o.get("activities"))
            targets=text_list(o.get("targetGroups"))
            languages=", ".join(str(x) for x in (o.get("languages") or []) if x)
            public_channels=source_list(o.get("publicChannels"),"Nincs külön igazolt közösségi profil rögzítve.")
            calendars=source_list(o.get("calendarSources"),"Nincs külön igazolt eseménynaptár vagy social programforrás rögzítve.")
            legacy_events=source_list(o.get("eventSources"),"Nincs külön legacy eseményforrás rögzítve.")
            evidence=source_list(o.get("evidenceSources"),"Még nincs külön háttérforrás rögzítve.")

            entity={"@type":"Organization","@id":url+"#entity","name":o.get("name"),"description":intro,"url":o.get("website") or url}
            same=[u for _,u in socials if u]
            if same:entity["sameAs"]=same
            if o.get("founded"):entity["foundingDate"]=o.get("founded")
            if o.get("email"):entity["email"]=o.get("email")
            if o.get("phone"):entity["telephone"]=o.get("phone")
            address={"@type":"PostalAddress","addressCountry":iso.upper()}
            if o.get("city"):address["addressLocality"]=o.get("city")
            if o.get("region") or o.get("state"):address["addressRegion"]=o.get("region") or o.get("state")
            if o.get("address"):address["streetAddress"]=o.get("address")
            entity["address"]=address
            if parent:entity["parentOrganization"]={"@type":"Organization","name":parent.get("name"),"url":f"{BASE}/countries/{iso}/organizations/{parent.get('id')}.html"}

            schema={"@context":"https://schema.org","@graph":[
                {"@type":"ProfilePage","@id":url+"#page","url":url,"name":title,"description":desc,"mainEntity":{"@id":url+"#entity"},"isPartOf":{"@id":BASE+"/#website"}},
                entity,
                {"@type":"BreadcrumbList","itemListElement":[
                    {"@type":"ListItem","position":1,"name":"DORAPP","item":BASE+"/"},
                    {"@type":"ListItem","position":2,"name":country_name,"item":f"{BASE}/countries/{iso}/"},
                    {"@type":"ListItem","position":3,"name":o.get("name"),"item":url}
                ]}
            ]}

            details=[]
            if o.get("city"):details.append(f'<strong>Város:</strong> {esc(o.get("city"))}')
            if o.get("region") or o.get("state"):details.append(f'<strong>Régió:</strong> {esc(o.get("region") or o.get("state"))}')
            if o.get("type"):details.append(f'<strong>Típus:</strong> {esc(o.get("type"))}')
            if o.get("legalForm"):details.append(f'<strong>Jogi forma:</strong> {esc(o.get("legalForm"))}')
            if o.get("registrationId"):details.append(f'<strong>Nyilvántartási azonosító:</strong> {esc(o.get("registrationId"))}')
            if languages:details.append(f'<strong>Nyelvek:</strong> {esc(languages)}')

            body=f'''<!doctype html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><link rel="icon" href="../../../favicon.svg" type="image/svg+xml"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large"><link rel="canonical" href="{url}"><meta property="og:type" content="profile"><meta property="og:title" content="{esc(o.get("name"))}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{url}"><link rel="stylesheet" href="../../../styles.css?v=20261001-country-parity"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace("</","<\\/")}</script></head><body><header class="topbar"><div class="wrap navrow"><a class="brand" href="../"><span class="mark">HU</span><span>DORAPP · {esc(country_name)}</span></a><nav><a href="../#terkep">Térkép</a><a href="../#kereso">Kereső</a><a href="../#kozossegek">Szervezetek</a><a href="../#programok">Programok</a></nav></div></header><main><section class="hero"><div class="wrap"><div class="eyebrow">{esc(" · ".join(str(x) for x in [o.get("region") or o.get("state"),o.get("city"),o.get("type")] if x))}</div><h1>{esc(o.get("name"))}</h1><p class="lead">{esc(intro)}</p><div class="hero-actions">{hero_actions}</div></div></section><section class="section muted"><div class="wrap trust-grid"><div><h2>Róluk röviden</h2></div><div><p>{esc(intro)}</p><p>{"<br>".join(details)}</p></div></div></section>{(f'<section class="section"><div class="wrap trust-grid"><div><h2>Történet</h2></div><div>{history_html}</div></div></section>' if history_html else '')}{(f'<section class="section muted"><div class="wrap trust-grid"><div><h2>Mit csinálnak?</h2></div><div>{activities}</div></div></section>' if activities else '')}{(f'<section class="section"><div class="wrap trust-grid"><div><h2>Kiknek szól?</h2></div><div>{targets}</div></div></section>' if targets else '')}<section class="section muted"><div class="wrap trust-grid"><div><h2>Kapcsolat</h2></div><div>{contact_html}</div></div></section>{(f'<section class="section"><div class="wrap trust-grid"><div><h2>Hol találkozhatsz velük?</h2></div><div>{service_html}</div></div></section>' if service_html else '')}<section class="section"><div class="wrap trust-grid"><div><h2>Kapcsolati háló</h2></div><div>{relation_html}</div></div></section><section class="section muted"><div class="wrap"><div class="section-head"><div><div class="eyebrow">A következő alkalmak</div><h2>Programok</h2></div></div>{events_html}</div></section><section class="section"><div class="wrap trust-grid"><div><h2>Hova töltik fel az eseményeiket?</h2></div><div>{calendars}</div></div></section><section class="section muted"><div class="wrap trust-grid"><div><h2>Automatikus / legacy eseményforrás</h2></div><div>{legacy_events}</div></div></section><section class="section"><div class="wrap trust-grid"><div><h2>Közösségi oldalak és nyilvános csatornák</h2></div><div>{public_channels}</div></div></section><section class="section muted"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Háttéranyagok</div><h2>Róluk írták.</h2></div></div>{article_html}</div></section><section class="section"><div class="wrap trust-grid"><div><h2>Ellenőrző források</h2></div><div>{evidence}</div></div></section></main><footer><div class="wrap footer-grid"><div><b>DORAPP</b><p>Forrásalapú magyar diaszpóra-címtár és programnaptár.</p></div><div><a href="../">Vissza {esc(country_name)} országoldalára</a></div><div><a href="../../../forrasok.html">Források és módszertan</a></div></div></footer><script src="../../../ui.js?v=20260926-consent-nav" defer></script></body></html>'''
            (out/f"{eid}.html").write_text(body,encoding="utf-8")
            generated+=1
    print(f"Generated rich worldwide organization profiles={generated}")

if __name__=="__main__":
    main()
