#!/usr/bin/env python3
from __future__ import annotations
import json,re,time,urllib.parse,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from html import unescape
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
ORG_FILE=ROOT/"data/organizations.json"
OUT_FILE=ROOT/"data/articles.json"
OLD_FILE=OUT_FILE
UA="Mozilla/5.0 (compatible; DORAPP-ArticleCurator/1.1; +https://github.com/880rzz/DORAPP)"

def clean(s):
    s=re.sub(r"<[^>]+>"," ",s or "")
    return re.sub(r"\s+"," ",unescape(s)).strip()

def fetch(url):
    last=None
    for attempt in range(2):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,*/*","Accept-Language":"hu,en;q=0.8,de;q=0.7"})
            with urllib.request.urlopen(req,timeout=8) as r:
                return r.read(2_000_000).decode(r.headers.get_content_charset() or "utf-8","replace")
        except Exception as ex:
            last=ex
            code=getattr(ex,"code",None)
            if attempt<1 and (code in (429,500,502,503,504) or code is None):
                time.sleep(1.5*(attempt+1))
                continue
            raise
    raise last

def norm(s):
    s=unescape(str(s or "")).casefold()
    s=re.sub(r"[^a-z0-9áéíóöőúüű]+"," ",s)
    return re.sub(r"\s+"," ",s).strip()

COMMON={"magyar","ausztriai","ausztria","becsi","bécsi","wien","vienna","egyesulet","egyesület","kulturalis","kulturális","kozosseg","közösség","klub","club","verein","gruppe","csoport","iskola","media","média"}

def rolunk_search(name):
    url="https://rolunk.at/?s="+urllib.parse.quote(name)
    html=fetch(url)
    found=[]
    name_tokens=[t for t in norm(name).split() if len(t)>=4 and t not in COMMON]
    if not name_tokens:
        return found
    for m in re.finditer(r'<a[^>]+href=["\'](https?://rolunk\.at/[^"\']+)["\'][^>]*>(.*?)</a>',html,re.I|re.S):
        u=m.group(1).split("#")[0]
        title=clean(m.group(2))
        path=urllib.parse.urlparse(u).path.strip("/")
        if not title or len(title)<8 or not path: continue
        if any(path.startswith(x) for x in ("category/","tag/","author/","wp-","feed","page/","korabbi-cikkek")): continue
        hay=norm(title+" "+urllib.parse.unquote(u))
        strong=[t for t in name_tokens if t in hay]
        if not strong:
            continue
        if u not in [x["url"] for x in found]:
            found.append({"title":title,"url":u,"source":"Rólunk.at"})
        if len(found)>=4: break
    return found

def main():
    db=json.loads(ORG_FILE.read_text(encoding="utf-8"))
    previous=json.loads(OLD_FILE.read_text(encoding="utf-8")) if OLD_FILE.exists() else {"articles":{}}
    previous_rows=previous.get("articles") or {}
    rows={}
    shard=datetime.now(timezone.utc).timetuple().tm_yday % 7
    def due_for_search(org_id):
        return sum(org_id.encode("utf-8")) % 7 == shard
    def build_articles(o):
        articles=[]
        evidence_urls={e.get("url") for e in o.get("evidenceSources",[]) if e.get("url")}
        if not due_for_search(o["id"]):
            for a in previous_rows.get(o["id"],[]):
                # Old automatic Rólunk.at search results are not carried forward
                # unless the URL is also an explicit evidence source. This
                # purges historic false-positive matches immediately.
                if a.get("source")=="Rólunk.at" and a.get("url") not in evidence_urls:
                    continue
                if a.get("url") and a["url"] not in [x["url"] for x in articles]:
                    articles.append(a)
        for e in o.get("evidenceSources",[]):
            u=e.get("url","")
            if any(d in u for d in ("rolunk.at/","volksgruppen.orf.at/","becsinaplo.at/","becsinaplo.eu/")):
                if u not in [x.get("url") for x in articles]:
                    articles.append({"title":e.get("label") or u,"url":u,"source":"Rólunk.at" if "rolunk.at" in u else ("ORF Volksgruppen" if "orf.at" in u else "Bécsi Napló")})
        if due_for_search(o["id"]):
            try:
                for a in rolunk_search(o["name"]):
                    if a["url"] not in [x["url"] for x in articles]:
                        articles.append(a)
            except Exception:
                pass
        return o["id"],articles[:6]

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures=[pool.submit(build_articles,o) for o in db["organizations"]]
        for future in as_completed(futures):
            org_id,articles=future.result()
            rows[org_id]=articles
    OUT_FILE.write_text(json.dumps({"updated":datetime.now(timezone.utc).isoformat(),"articles":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("organizations=",len(rows),"with_articles=",sum(bool(v) for v in rows.values()),"search_shard=",shard)

if __name__=="__main__": main()
