#!/usr/bin/env python3
import json, re, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
READY=DATA/"promotion-ready.json"

def now_date():
    return datetime.now(timezone.utc).date().isoformat()

def slug(s):
    import unicodedata
    s=unicodedata.normalize("NFKD",str(s)).encode("ascii","ignore").decode("ascii").lower()
    s=re.sub(r"[^a-z0-9]+","-",s).strip("-")
    return s[:90] or "entity"

def read(path,default):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return default

def entity_class(t):
    if t in {"EducationalOrganization","School","CollegeOrUniversity"}: return "institution"
    if t=="Church": return "organization"
    if t=="Library": return "institution"
    if t=="PerformingGroup": return "group"
    return "organization"

def main():
    if not READY.exists():
        print("No promotion-ready queue")
        return
    ready=read(READY,{"items":[]})
    promoted=0
    for x in ready.get("items",[]):
        iso=x.get("country")
        if not iso or not x.get("name") or not x.get("website") or not x.get("city"):
            continue
        p=DATA/"countries"/iso/"organizations.json"
        doc=read(p,{
          "updated":now_date(),
          "sourcePolicy":"Only first-party verified organizations are canonical; unknown facts remain empty.",
          "organizations":[]
        })
        items=doc.setdefault("organizations",[])
        host=urllib.parse.urlparse(x["website"]).netloc.lower().removeprefix("www.")
        existing=None
        for o in items:
            oh=urllib.parse.urlparse(o.get("website") or "").netloc.lower().removeprefix("www.")
            if oh and oh==host:
                existing=o;break
            if o.get("name","").casefold()==x["name"].casefold() and o.get("city")==x.get("city"):
                existing=o;break
        if existing:
            continue
        base=slug(x["name"])
        used={o.get("id") for o in items}
        eid=base
        n=2
        while eid in used:
            eid=f"{base}-{n}";n+=1
        rec={
          "id":eid,
          "name":x["name"],
          "country":iso,
          "region":x.get("region"),
          "city":x.get("city"),
          "type":x.get("entityType"),
          "entityClass":entity_class(x.get("entityType")),
          "website":x["website"],
          "profileVerifiedAt":x.get("verifiedAt"),
          "evidenceSources":[
             {"label":"Official website","url":x["website"],"type":"official"},
             {"label":"Discovery source","url":x.get("secondaryUrl"),"type":"secondary"}
          ]
        }
        rec["evidenceSources"]=[e for e in rec["evidenceSources"] if e.get("url")]
        items.append(rec)
        items.sort(key=lambda o:(str(o.get("city") or ""),str(o.get("name") or "")))
        doc["updated"]=now_date()
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        promoted+=1
    print(f"Canonical promotions={promoted}")

if __name__=="__main__":
    main()
