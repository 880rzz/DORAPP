#!/usr/bin/env python3
import json, re, html as htmlmod, urllib.parse, urllib.request
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
GLOBAL=DATA/"global.json"
QUEUE=DATA/"verification-queue.json"
READY=DATA/"promotion-ready.json"
UA="DORAPP-Global-Steward/1.0 (+https://diaszpora.kozpontiszovetseg.at/)"
TIMEOUT=20
MAX_ITEMS=40
ORG_TYPES={"Organization","EducationalOrganization","School","CollegeOrUniversity","NGO","PerformingGroup","Church","Library"}

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def norm(s):
    return re.sub(r"\s+"," ",str(s or "")).strip().lower()

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
        ctype=(r.headers.get("content-type") or "").lower()
        if "html" not in ctype:
            return r.geturl(),"",""
        raw=r.read(1500000).decode("utf-8","replace")
        return r.geturl(),raw,ctype

def strip_html(raw):
    text=re.sub(r"(?is)<script\b.*?</script>"," ",raw)
    text=re.sub(r"(?is)<style\b.*?</style>"," ",text)
    text=re.sub(r"(?s)<[^>]+>"," ",text)
    return norm(htmlmod.unescape(text))

def jsonld_objects(raw):
    objs=[]
    for m in re.finditer(r'(?is)<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',raw):
        try:
            data=json.loads(htmlmod.unescape(m.group(1)).strip())
        except Exception:
            continue
        stack=data if isinstance(data,list) else [data]
        while stack:
            x=stack.pop()
            if isinstance(x,dict):
                objs.append(x)
                g=x.get("@graph")
                if isinstance(g,list): stack.extend(g)
            elif isinstance(x,list):
                stack.extend(x)
    return objs

def type_set(x):
    t=x.get("@type")
    if isinstance(t,str): return {t}
    if isinstance(t,list): return set(str(v) for v in t)
    return set()

def address_parts(x):
    a=x.get("address")
    if isinstance(a,str):
        return {"streetAddress":a}
    if not isinstance(a,dict):
        loc=x.get("location")
        if isinstance(loc,dict):
            a=loc.get("address")
    return a if isinstance(a,dict) else {}

def country_match(address_country,iso,names,text):
    ac=norm(address_country)
    values={norm(iso),norm(iso.upper())}
    for v in names.values():
        if isinstance(v,str): values.add(norm(v))
    if ac and any(ac==v or ac in v or v in ac for v in values if v):
        return True
    return any(v and len(v)>3 and v in text for v in values)

def identity_tokens(title):
    stop={"hungarian","magyar","association","community","school","church","club","society","of","the","in","and","egyesulet","kozosseg","iskola"}
    return {x for x in re.findall(r"[a-zA-ZÀ-ž0-9]{4,}",norm(title)) if x not in stop}

def verify_item(item,c,checked):
    iso=item.get("country")
    names=c.get("name") or {}
    tokens=identity_tokens(item.get("title"))
    best=None
    for url in item.get("firstPartyCandidates",[])[:8]:
        try:
            final_url,raw,_=fetch(url)
            text=strip_html(raw)
            if not text:
                continue
            org_signal=bool(re.search(r"\b(hungarian|magyar)\b",text)) and bool(re.search(r"\b(association|community|school|church|club|society|cultural|scout|choir|theatre|foundation|center|centre|egyesulet|kozosseg|iskola|templom|cserkesz)\b",text))
            token_hits=sum(1 for t in tokens if t in text)
            for obj in jsonld_objects(raw):
                types=type_set(obj)&ORG_TYPES
                if not types:
                    continue
                name=obj.get("name")
                if not name:
                    continue
                addr=address_parts(obj)
                addr_country=addr.get("addressCountry")
                if isinstance(addr_country,dict):
                    addr_country=addr_country.get("name")
                locality=addr.get("addressLocality")
                region=addr.get("addressRegion")
                if not country_match(addr_country,iso,names,text):
                    continue
                identity_ok=token_hits>=1 or norm(name) in text
                score=(3 if org_signal else 0)+(2 if identity_ok else 0)+(2 if locality else 0)+(1 if region else 0)
                candidate={
                  "country":iso,
                  "name":name,
                  "entityType":next(iter(types)),
                  "website":final_url,
                  "city":locality,
                  "region":region,
                  "addressCountry":addr_country or iso.upper(),
                  "secondaryUrl":item.get("secondaryUrl"),
                  "verifiedAt":checked,
                  "verificationScore":score,
                  "verificationMethod":"first-party HTML + JSON-LD organization + country match",
                }
                if not best or candidate["verificationScore"]>best["verificationScore"]:
                    best=candidate
        except Exception:
            continue

    if best and best["verificationScore"]>=7 and best.get("city"):
        item["firstPartyStatus"]="verified-promotion-ready"
        item["firstPartyVerifiedAt"]=checked
        item["verifiedUrl"]=best["website"]
        return best
    if best:
        item["firstPartyStatus"]="verified-partial"
        item["firstPartyVerifiedAt"]=checked
        item["verifiedUrl"]=best["website"]
        return None
    item["firstPartyStatus"]="no-strong-first-party-proof"
    item["firstPartyVerifiedAt"]=checked
    return None

def main():
    if not QUEUE.exists():
        print("No verification queue yet")
        return
    g=json.loads(GLOBAL.read_text(encoding="utf-8"))
    by={c["iso2"]:c for c in g.get("countries",[])}
    q=json.loads(QUEUE.read_text(encoding="utf-8"))
    checked=now_iso()
    ready=[]
    work=[]
    for item in q.get("items",[]):
        if len(work)>=MAX_ITEMS:
            break
        iso=item.get("country")
        country=by.get(iso)
        if country:
            work.append((item,country))

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures={pool.submit(verify_item,item,country,checked):item for item,country in work}
        for future in as_completed(futures):
            try:
                candidate=future.result()
                if candidate:
                    ready.append(candidate)
            except Exception:
                item=futures[future]
                item["firstPartyStatus"]="verification-error"
                item["firstPartyVerifiedAt"]=checked

    processed=len(work)
    q["updated"]=checked
    QUEUE.write_text(json.dumps(q,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    existing=[]
    if READY.exists():
        try: existing=json.loads(READY.read_text(encoding="utf-8")).get("items",[])
        except Exception: pass
    key=lambda x:(x.get("country"),norm(x.get("name")),urllib.parse.urlparse(x.get("website") or "").netloc.lower())
    merged={key(x):x for x in existing}
    for x in ready: merged[key(x)]=x
    READY.write_text(json.dumps({"updated":checked,"items":sorted(merged.values(),key=lambda x:(x.get("country",""),norm(x.get("name"))))},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"First-party verification processed={processed}; promotion-ready={len(ready)}")

if __name__=="__main__":
    main()
