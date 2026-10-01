#!/usr/bin/env python3
import json, ssl, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
GLOBAL=DATA/"global.json"
UA="DORAPP-Source-Health/1.0 (+https://diaszpora.kozpontiszovetseg.at/)"
TIMEOUT=18

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def read(path,default):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return default

def check(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml"})
    try:
        with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
            code=getattr(r,"status",200)
            ctype=(r.headers.get("content-type") or "").lower()
            final=r.geturl()
            if code==429:
                return "rate-limited",code,final,ctype
            if code in (401,403):
                return "site-blocked",code,final,ctype
            if code>=400:
                return "http-error",code,final,ctype
            if "html" in ctype:
                return "ok",code,final,ctype
            if any(kind in ctype for kind in ("application/pdf","application/json","application/xml","text/xml","text/plain","application/rss+xml","application/atom+xml")):
                return "ok-non-html",code,final,ctype
            return "parser-gap",code,final,ctype
    except urllib.error.HTTPError as e:
        if e.code==429:return "rate-limited",e.code,url,""
        if e.code in (401,403):return "site-blocked",e.code,url,""
        return "http-error",e.code,url,""
    except ssl.SSLError:
        return "tls-error",None,url,""
    except urllib.error.URLError as e:
        reason=str(getattr(e,"reason","")).lower()
        if "timed out" in reason:return "timeout",None,url,""
        if "ssl" in reason or "certificate" in reason:return "tls-error",None,url,""
        return "network-error",None,url,""
    except TimeoutError:
        return "timeout",None,url,""
    except Exception:
        return "network-error",None,url,""

def main():
    g=read(GLOBAL,{"countries":[]})
    checked=now_iso()
    total=0
    bad=0
    for c in g.get("countries",[]):
        iso=c.get("iso2")
        if iso=="at": continue
        org_path=DATA/"countries"/iso/"organizations.json"
        if not org_path.exists(): continue
        org=read(org_path,{"organizations":[]})
        rows=[]
        for o in org.get("organizations",[]):
            url=o.get("website")
            source_role="official-website"
            if not url:
                trusted={"official","government","institutional","registry","first-party-person"}
                evidence=[e for e in (o.get("evidenceSources") or []) if e.get("url") and e.get("type") in trusted]
                if evidence:
                    url=evidence[0]["url"]
                    source_role="primary-evidence"
            if not url:
                rows.append({
                  "id":o.get("id"),
                  "url":None,
                  "sourceRole":"none",
                  "status":"no-verifiable-web-source",
                  "httpStatus":None,
                  "resolvedUrl":None,
                  "contentType":"",
                  "checkedAt":checked,
                  "removalAuthority":False,
                  "note":"No web source is available; this is a data-quality review condition, not removal evidence."
                })
                bad+=1
                total+=1
                continue
            status,code,final,ctype=check(url)
            total+=1
            if status not in {"ok","ok-non-html"}: bad+=1
            rows.append({
              "id":o.get("id"),
              "url":url,
              "sourceRole":source_role,
              "status":status,
              "httpStatus":code,
              "resolvedUrl":final,
              "contentType":ctype,
              "checkedAt":checked,
              "removalAuthority":False,
              "note":(
                "Reachable non-HTML evidence source; availability is healthy, content parsing is format-specific."
                if status=="ok-non-html" else
                "Reachable source with an unsupported content type; parser coverage is missing, not source validity."
                if status=="parser-gap" else
                "Technical failure alone is never evidence for entity removal."
                if status!="ok" else None
              )
            })
        if rows:
            out=DATA/"countries"/iso/"source-health.json"
            out.write_text(json.dumps({"updated":checked,"sources":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Global source health checked={total}; non-ok={bad}")

if __name__=="__main__":
    main()
