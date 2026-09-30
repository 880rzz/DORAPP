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

def main():
    g=json.loads(GLOBAL.read_text(encoding="utf-8"))
    state=json.loads(STATE.read_text(encoding="utf-8"))
    by={c["iso2"]:c for c in g.get("countries",[])}
    attempted=state.get("countriesAttempted",[])
    checked=now_iso()
    queue=[]

    for iso in attempted:
        c=by.get(iso,{})
        names=c.get("name") or {}
        country_terms=[norm(names.get("en")),norm(names.get("hu")),norm(names.get("officialEn"))]
        country_terms=[x for x in country_terms if x and len(x)>2]
        p=DATA/"countries"/iso/"discovery-sources.json"
        if not p.exists():
            continue
        doc=json.loads(p.read_text(encoding="utf-8"))
        for item in doc.get("sources",[]):
            if item.get("sourceType")!="wikipedia-discovery":
                continue
            try:
                result=api(item.get("language") or "en",item.get("title") or "")
                pages=((result.get("query") or {}).get("pages") or {})
                page=next(iter(pages.values())) if pages else {}
                text=norm((item.get("title") or "")+" "+(page.get("extract") or ""))
                hungarian=bool(re.search(r"\b(hungarian|hungarians|magyar|magyars)\b",text))
                country_hit=any(t in text for t in country_terms)
                links=external_links(page)
                score=(2 if hungarian else 0)+(2 if country_hit else 0)+(1 if links else 0)
                item["verificationCheckedAt"]=checked
                item["verificationScore"]=score
                item["firstPartyCandidates"]=links[:8]
                if score>=4 and links:
                    item["status"]="first-party-review"
                    queue.append({
                      "country":iso,
                      "countryName":names.get("en") or iso.upper(),
                      "title":item.get("title"),
                      "secondaryUrl":item.get("url"),
                      "firstPartyCandidates":links[:8],
                      "score":score
                    })
                elif score>=4:
                    item["status"]="secondary-qualified"
                else:
                    item["status"]="rejected-low-signal"
            except Exception as e:
                item["verificationCheckedAt"]=checked
                item["verificationError"]=type(e).__name__
        doc["verificationUpdated"]=checked
        p.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    existing={"updated":checked,"items":[]}
    if QUEUE.exists():
        try: existing=json.loads(QUEUE.read_text(encoding="utf-8"))
        except Exception: pass
    key=lambda x:(x.get("country"),x.get("title"),x.get("secondaryUrl"))
    merged={key(x):x for x in existing.get("items",[]) if x.get("country")}
    for x in queue: merged[key(x)]=x
    QUEUE.write_text(json.dumps({"updated":checked,"items":sorted(merged.values(),key=key)},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Verification queue updated: {len(queue)} strong candidates from current batch")

if __name__=="__main__":
    main()
