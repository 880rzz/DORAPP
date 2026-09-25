#!/usr/bin/env python3
from __future__ import annotations
import json,re,urllib.parse,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from html import unescape
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
ORG_FILE=ROOT/"data/organizations.json"
OUT_FILE=ROOT/"data/articles.json"
UA="DORAPP-ArticleCurator/1.0 (+https://github.com/880rzz/DORAPP)"

def clean(s):
    s=re.sub(r"<[^>]+>"," ",s or "")
    return re.sub(r"\s+"," ",unescape(s)).strip()

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,*/*"})
    with urllib.request.urlopen(req,timeout=8) as r:
        return r.read(2_000_000).decode(r.headers.get_content_charset() or "utf-8","replace")

def rolunk_search(name):
    url="https://rolunk.at/?s="+urllib.parse.quote(name)
    html=fetch(url)
    found=[]
    for m in re.finditer(r'<a[^>]+href=["\'](https?://rolunk\.at/[^"\']+)["\'][^>]*>(.*?)</a>',html,re.I|re.S):
        u=m.group(1).split("#")[0]
        title=clean(m.group(2))
        path=urllib.parse.urlparse(u).path.strip("/")
        if not title or len(title)<8 or not path: continue
        if any(path.startswith(x) for x in ("category/","tag/","author/","wp-","feed","page/","korabbi-cikkek")): continue
        if u not in [x["url"] for x in found]:
            found.append({"title":title,"url":u,"source":"Rólunk.at"})
        if len(found)>=4: break
    return found

def main():
    db=json.loads(ORG_FILE.read_text(encoding="utf-8"))
    rows={}
    def build_articles(o):
        articles=[]
        for e in o.get("evidenceSources",[]):
            u=e.get("url","")
            if any(d in u for d in ("rolunk.at/","volksgruppen.orf.at/","becsinaplo.at/","becsinaplo.eu/")):
                articles.append({"title":e.get("label") or u,"url":u,"source":"Rólunk.at" if "rolunk.at" in u else ("ORF Volksgruppen" if "orf.at" in u else "Bécsi Napló")})
        try:
            for a in rolunk_search(o["name"]):
                if a["url"] not in [x["url"] for x in articles]:
                    articles.append(a)
        except Exception:
            pass
        return o["id"],articles[:6]

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures=[pool.submit(build_articles,o) for o in db["organizations"]]
        for future in as_completed(futures):
            org_id,articles=future.result()
            rows[org_id]=articles
    OUT_FILE.write_text(json.dumps({"updated":datetime.now(timezone.utc).isoformat(),"articles":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("organizations=",len(rows),"with_articles=",sum(bool(v) for v in rows.values()))

if __name__=="__main__": main()
