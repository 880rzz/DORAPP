#!/usr/bin/env python3
import json, re, urllib.parse, urllib.request
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
GLOBAL=DATA/"global.json"
STATE=DATA/"research-state.json"
QUEUE=DATA/"verification-queue.json"
UA="DORAPP-Global-Steward/1.0 (+https://diaszpora.kozpontiszovetseg.at/)"
TIMEOUT=20
EXCLUDED=("wikipedia.org","wikimedia.org","facebook.com","instagram.com","youtube.com","linkedin.com","tiktok.com","x.com","twitter.com")
ENTITY_RE=re.compile(r"\b(association|society|community|church|parish|school|college|university|club|scout|scouts|federation|foundation|cultural centre|cultural center|choir|theatre|theater|institute|institution|library|egyesulet|egyesület|kozosseg|közösség|iskola|ovoda|óvoda|cserkesz|cserkész|szovetseg|szövetség|alapitvany|alapítvány|intezet|intézet|templom|gyulekezet|gyülekezet)\b",re.I)
PERSONISH_RE=re.compile(r"\b(born|died|footballer|player|coach|politician|writer|actor|actress|artist|athlete|composer|was a|is a)\b",re.I)

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def api(lang,title):
    params={
      "action":"query","format":"json","redirects":"1","prop":"extracts|extlinks",
      "exintro":"1","explaintext":"1","ellimit":"max","titles":title
    }
    url=f"https://{lang}.wikipedia.org/w/api.php?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))

def external_links(page):
    out=[]
    for x in page.get("extlinks",[]) or []:
        u=x.get("*") or x.get("url")
        if not u or not u.startswith("http"):
            continue
        host=urllib.parse.urlparse(u).netloc.lower().removeprefix("www.")
        if any(host==d or host.endswith("."+d) for d in EXCLUDED):
            continue
        out.append(u)
    return sorted(set(out))

def norm(s):
    return re.sub(r"\s+"," ",str(s or "")).strip().lower()

def country_terms(c):
    vals=[]
    for v in (c.get("name") or {}).values():
        if isinstance(v,str) and len(v.strip())>3:
            vals.append(norm(v))
    vals.extend(norm(v) for v in c.get("aliases",[]) if isinstance(v,str) and len(v.strip())>3)
    return sorted(set(vals))

def qualified_item(item,c,checked):
    result=api(item.get("language") or "en",item.get("title") or "")
    pages=((result.get("query") or {}).get("pages") or {})
    page=next(iter(pages.values())) if pages else {}
    extract=page.get("extract") or ""
    text=norm((item.get("title") or "")+" "+extract)
    hungarian=bool(re.search(r"\b(hungarian|hungarians|magyar|magyars)\b",text,re.I))
    country_hit=any(t in text for t in country_terms(c))
    entity_signal=bool(ENTITY_RE.search(text))
    personish=bool(PERSONISH_RE.search(extract[:700])) and not bool(ENTITY_RE.search(item.get("title") or ""))
    links=external_links(page)
    score=(2 if hungarian else 0)+(2 if country_hit else 0)+(3 if entity_signal else 0)+(1 if links else 0)-(3 if personish else 0)
    item["verificationCheckedAt"]=checked
    item["verificationScore"]=score
    item["firstPartyCandidates"]=links[:8]
    item["entitySignal"]=entity_signal
    item["countrySignal"]=country_hit
    item["hungarianSignal"]=hungarian
    if hungarian and country_hit and entity_signal and not personish and links and score>=7:
        item["status"]="first-party-review"
        return {
          "country":c["iso2"],
          "countryName":(c.get("name") or {}).get("en") or c["iso2"].upper(),
          "title":item.get("title"),
          "secondaryUrl":item.get("url"),
          "firstPartyCandidates":links[:8],
          "score":score
        }
    if hungarian and country_hit and entity_signal and not personish:
        item["status"]="secondary-qualified"
    else:
        item["status"]="rejected-low-signal"
    return None

def main():
    g=json.loads(GLOBAL.read_text(encoding="utf-8"))
    state=json.loads(STATE.read_text(encoding="utf-8"))
    by={c["iso2"]:c for c in g.get("countries",[])}
    attempted=state.get("countriesAttempted",[])
    checked=now_iso()
    current=[]

    for iso in attempted:
        c=by.get(iso)
        if not c: continue
        p=DATA/"countries"/iso/"discovery-sources.json"
        if not p.exists(): continue
        doc=json.loads(p.read_text(encoding="utf-8"))
        for item in doc.get("sources",[]):
            if item.get("sourceType")!="wikipedia-discovery":
                continue
            try:
                q=qualified_item(item,c,checked)
                if q: current.append(q)
            except Exception as e:
                item["verificationCheckedAt"]=checked
                item["verificationError"]=type(e).__name__
        doc["verificationUpdated"]=checked
        p.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    # Rebuild the global review queue only from candidates that still pass the
    # stricter entity/country/Hungarian gate. This intentionally drops stale,
    # person-like and generic historical candidates from earlier runs.
    all_items=[]
    for c in g.get("countries",[]):
        p=DATA/"countries"/c["iso2"]/"discovery-sources.json"
        if not p.exists(): continue
        try: doc=json.loads(p.read_text(encoding="utf-8"))
        except Exception: continue
        for item in doc.get("sources",[]):
            if item.get("status")!="first-party-review":
                continue
            links=item.get("firstPartyCandidates") or []
            if not links: continue
            all_items.append({
              "country":c["iso2"],
              "countryName":(c.get("name") or {}).get("en") or c["iso2"].upper(),
              "title":item.get("title"),
              "secondaryUrl":item.get("url"),
              "firstPartyCandidates":links[:8],
              "score":item.get("verificationScore")
            })

    key=lambda x:(x.get("country"),x.get("title"),x.get("secondaryUrl"))
    dedup={key(x):x for x in all_items}
    QUEUE.write_text(json.dumps({"updated":checked,"items":sorted(dedup.values(),key=key)},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Verification queue rebuilt: current strong={len(current)}, total strong={len(dedup)}")

if __name__=="__main__":
    main()
