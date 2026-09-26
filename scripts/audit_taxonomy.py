#!/usr/bin/env python3
from __future__ import annotations
import json,re,urllib.request,urllib.parse
from pathlib import Path
from html import unescape
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
ORG=ROOT/"data/organizations.json"
EDU=ROOT/"data/education.json"
EV=ROOT/"data/events.json"
OUT=ROOT/"data/taxonomy-audit.json"
UA="DORAPP-TaxonomyAudit/1.0 (+https://github.com/880rzz/DORAPP)"

SIGNALS={
 "oktatas":[r"iskola",r"schule",r"unterricht",r"oktat",r"kurs",r"tanfolyam",r"pedag"],
 "neptanc":[r"néptánc",r"neptanc",r"volkstanz",r"tánccsoport"],
 "nepzene":[r"népzene",r"volksmusik",r"citera",r"hegedű",r"zenekar"],
 "enekkar":[r"énekkar",r"ének.?kör",r"népdalkör",r"dalárda",r"chor",r"singkreis"],
 "cserkesz":[r"cserkész",r"scout"],
 "szinhaz":[r"színház",r"színjáts",r"dráma",r"theater",r"musical"],
 "media":[r"média",r"media",r"információs központ",r"magazin",r"rádió",r"radio",r"újság",r"zeitung",r"redak",r"sajtó"],
 "egyhaz":[r"katol",r"reform",r"evang",r"templom",r"kirche",r"pfarre"],
 "diak":[r"diák",r"student",r"egyetemista",r"alumni"],
 "irodalom":[r"irodal",r"könyv",r"literatur",r"olvas"],
 "muveszet":[r"művész",r"kunst",r"fotó",r"photo",r"kiállítás"],
 "sport":[r"sport",r"futás",r"lauf",r"labdarúg",r"tenisz"],
 "csalad":[r"család",r"famil",r"baba",r"gyermek",r"kinder"],
}
ACTIVITY_HINTS=[r"foglalkoz",r"tanfolyam",r"kurzus",r"workshop",r"óra",r"event-details",r"heti ",r"kéthetente"]
OLD_LEVEL_CATS={"bolcsode","ovoda","iskola","felsooktatas","gyermek","ifjusag","nephagyomany","zene"}

def clean(raw:str)->str:
    raw=re.sub(r"<script\b[^>]*>.*?</script>"," ",raw,flags=re.I|re.S)
    raw=re.sub(r"<style\b[^>]*>.*?</style>"," ",raw,flags=re.I|re.S)
    raw=re.sub(r"<[^>]+>"," ",raw)
    return re.sub(r"\s+"," ",unescape(raw)).strip()

def fetch(url:str)->str:
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,*/*;q=0.8"})
    with urllib.request.urlopen(req,timeout=7) as r:
        if r.headers.get_content_type() not in ("text/html","application/xhtml+xml"):
            return ""
        return clean(r.read(1_500_000).decode(r.headers.get_content_charset() or "utf-8","replace"))

def org_urls(o):
    urls=[]
    for u in [o.get("website"),*(o.get("eventSources") or [])]:
        if u and u.startswith(("http://","https://")) and u not in urls: urls.append(u)
    for e in o.get("evidenceSources") or []:
        u=e.get("url")
        if u and u.startswith(("http://","https://")) and u not in urls: urls.append(u)
    return urls[:3]

def audit_org(o):
    texts=[];checked=[];errors=[]
    for u in org_urls(o):
        try:
            t=fetch(u)
            if t: texts.append(t);checked.append(u)
        except Exception as ex:
            errors.append({"url":u,"error":str(ex)[:160]})
    hay=(" ".join([o.get("name",""),o.get("type",""),o.get("intro",""),*texts])).casefold()
    signals=[k for k,patterns in SIGNALS.items() if any(re.search(p,hay,re.I) for p in patterns)]
    flags=[]
    cats=set(o.get("categories") or [])
    if o.get("entityClass")=="activity" and cats:
        flags.append("activity-has-entity-categories")
    if cats & OLD_LEVEL_CATS:
        flags.append("legacy-offering-category-on-entity")
    if o.get("entityClass")!="activity":
        own_activity_hint=any(re.search(p,(o.get("type","")+" "+o.get("name","")+" "+(o.get("website") or "")).casefold(),re.I) for p in ACTIVITY_HINTS)
        if own_activity_hint and o.get("parentOrganizationId") and o.get("classificationOverride")!="stable-group":
            flags.append("possible-activity-classification")
    for cat in cats:
        if cat in SIGNALS and cat not in signals and checked:
            flags.append(f"weak-source-signal:{cat}")
    return {
      "id":o["id"],"name":o["name"],"entityClass":o.get("entityClass"),
      "categories":sorted(cats),"activityCategories":o.get("activityCategories") or [],
      "signals":signals,"pagesChecked":len(checked),"checkedUrls":checked,"errors":errors,"flags":sorted(set(flags))
    }

def main():
    orgdb=json.loads(ORG.read_text(encoding="utf-8"))
    edudb=json.loads(EDU.read_text(encoding="utf-8"))
    evdb=json.loads(EV.read_text(encoding="utf-8"))
    rows=[]
    with ThreadPoolExecutor(max_workers=12) as pool:
        futs=[pool.submit(audit_org,o) for o in orgdb.get("organizations",[])]
        for f in as_completed(futs):
            rows.append(f.result())
    rows.sort(key=lambda x:x["id"])
    edu_flags=[]
    for x in edudb.get("institutions",[]):
        flags=[]
        if not x.get("level"): flags.append("missing-level")
        if not x.get("sourceUrl"): flags.append("missing-source")
        if x.get("verifiedFor") and x.get("verifiedPeriod") and x["verifiedFor"]!=x["verifiedPeriod"]:
            flags.append("conflicting-verified-period")
        if flags: edu_flags.append({"id":x.get("id"),"name":x.get("name"),"flags":flags})
    event_flags=[]
    for e in evdb.get("events",[]):
        flags=[]
        if not e.get("programCategories"): flags.append("missing-program-category")
        if not e.get("sourceUrl"): flags.append("missing-source")
        if flags:event_flags.append({"id":e.get("id"),"name":e.get("name"),"flags":flags})
    result={
      "updated":datetime.now(timezone.utc).isoformat(),
      "summary":{
        "organizations":len(rows),
        "organizationFlags":sum(bool(x["flags"]) for x in rows),
        "organizationPagesChecked":sum(x["pagesChecked"] for x in rows),
        "education":len(edudb.get("institutions",[])),
        "educationFlags":len(edu_flags),
        "events":len(evdb.get("events",[])),
        "eventFlags":len(event_flags)
      },
      "organizations":rows,
      "educationFlags":edu_flags,
      "eventFlags":event_flags
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result["summary"],ensure_ascii=False))

if __name__=="__main__":
    main()
