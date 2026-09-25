#!/usr/bin/env python3
from __future__ import annotations
import json,re,urllib.parse,urllib.request
from pathlib import Path
from datetime import datetime,timezone
from html import unescape
from concurrent.futures import ThreadPoolExecutor,as_completed

ROOT=Path(__file__).resolve().parents[1]
EDU=ROOT/"data/education.json"
OUT=ROOT/"data/education-site-health.json"
UA="DORAPP-EducationSiteAudit/1.0 (+https://github.com/880rzz/DORAPP)"
TERMS={
 "hungarian":["ungarisch","magyar","hungarian"],
 "bilingual":["zweisprach","bilingual","kétnyelv"],
 "first_language":["erstsprach","muttersprach","herkunftssprach","elsőnyelv"],
 "minority":["minderheit","volksgruppe","népcsoport"]
}
LINK_HINT=re.compile(r"(ungar|magyar|sprach|language|unterricht|angebot|bildung|kindergarten|schule|stud|kurs|programm)",re.I)

def clean_html(raw:str)->str:
    raw=re.sub(r"<script\b[^>]*>.*?</script>"," ",raw,flags=re.I|re.S)
    raw=re.sub(r"<style\b[^>]*>.*?</style>"," ",raw,flags=re.I|re.S)
    raw=re.sub(r"<[^>]+>"," ",raw)
    return re.sub(r"\s+"," ",unescape(raw)).strip()

def fetch(url:str)->tuple[str,str]:
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml,*/*;q=0.8"})
    with urllib.request.urlopen(req,timeout=10) as r:
        raw=r.read(2_000_000)
        ct=r.headers.get_content_type()
        return raw.decode(r.headers.get_content_charset() or "utf-8","replace"),ct

def internal_links(html:str,base:str)->list[str]:
    host=urllib.parse.urlparse(base).netloc
    out=[]
    for href in re.findall(r'href=["\']([^"\']+)["\']',html,re.I):
        u=urllib.parse.urljoin(base,unescape(href))
        p=urllib.parse.urlparse(u)
        if p.scheme not in ("http","https") or p.netloc!=host: continue
        if LINK_HINT.search(p.path+"?"+p.query) and u not in out:
            out.append(u)
    return out[:8]

def matches(text:str):
    low=text.casefold()
    found={}
    for group,terms in TERMS.items():
        hits=[t for t in terms if t.casefold() in low]
        if hits: found[group]=hits
    return found

def audit(inst):
    url=inst.get("website")
    row={
      "id":inst["id"],"name":inst["name"],"website":url,
      "checkedAt":datetime.now(timezone.utc).isoformat(),
      "status":"no-website" if not url else "unknown",
      "pagesChecked":0,"matches":{},"matchedUrls":[]
    }
    if not url:return row
    try:
        html,ct=fetch(url);row["pagesChecked"]=1
        if ct not in ("text/html","application/xhtml+xml"):
            row["status"]="non-html";return row
        page_matches=matches(clean_html(html))
        if page_matches:
            row["matches"]=page_matches;row["matchedUrls"].append(url)
        for u in internal_links(html,url):
            try:
                sub,subct=fetch(u);row["pagesChecked"]+=1
                if subct not in ("text/html","application/xhtml+xml"):continue
                m=matches(clean_html(sub))
                if m:
                    row["matchedUrls"].append(u)
                    for k,v in m.items():
                        row["matches"].setdefault(k,[])
                        row["matches"][k]=sorted(set(row["matches"][k]+v))
            except Exception:
                continue
        row["status"]="relevant-content-found" if row["matchedUrls"] else "reachable-no-relevant-keywords"
    except Exception as ex:
        row["status"]="error";row["error"]=str(ex)[:220]
    return row

def main():
    db=json.loads(EDU.read_text(encoding="utf-8"))
    rows=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures=[pool.submit(audit,x) for x in db.get("institutions",[])]
        for f in as_completed(futures): rows.append(f.result())
    rows.sort(key=lambda x:x["id"])
    now=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps({"updated":now,"sites":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("institutions=",len(rows),
          "relevant=",sum(x["status"]=="relevant-content-found" for x in rows),
          "no_relevant=",sum(x["status"]=="reachable-no-relevant-keywords" for x in rows),
          "no_website=",sum(x["status"]=="no-website" for x in rows),
          "errors=",sum(x["status"]=="error" for x in rows))

if __name__=="__main__": main()
