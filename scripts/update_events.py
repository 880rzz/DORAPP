#!/usr/bin/env python3
from __future__ import annotations
import json,re,urllib.request,urllib.parse
from pathlib import Path
from datetime import datetime,timezone,timedelta
from html import unescape

ROOT=Path(__file__).resolve().parents[1]
ORG_FILE=ROOT/"data/organizations.json"
EVENT_FILE=ROOT/"data/events.json"
HEALTH_FILE=ROOT/"data/source-health.json"
UA="AustriaHungarianProgramDirectory/1.1 (+https://github.com/880rzz/okoszisztema)"
EVENT_HINT=re.compile(r"(event|events|event-details|veranstaltung|termine|program|programme|esemeny|rendezveny|calendar)",re.I)

def fetch(url:str)->tuple[str,str]:
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml,text/calendar,application/json;q=0.9,*/*;q=0.8"})
    with urllib.request.urlopen(req,timeout=25) as r:
        raw=r.read(3_000_000)
        ct=r.headers.get_content_type()
        return raw.decode(r.headers.get_content_charset() or "utf-8","replace"),ct

def jsonld_blocks(html:str):
    for b in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',html,re.I|re.S):
        try: yield json.loads(unescape(b).strip())
        except Exception: continue

def walk(obj):
    if isinstance(obj,dict):
        yield obj
        for v in obj.values(): yield from walk(v)
    elif isinstance(obj,list):
        for v in obj: yield from walk(v)

def is_event(x):
    t=x.get("@type")
    return t=="Event" or (isinstance(t,list) and "Event" in t)

def addr_text(location):
    if not isinstance(location,dict): return None,None
    venue=location.get("name"); a=location.get("address")
    if isinstance(a,str): return venue,a
    if isinstance(a,dict):
        bits=[a.get("streetAddress"),a.get("postalCode"),a.get("addressLocality"),a.get("addressRegion"),a.get("addressCountry")]
        return venue,", ".join(str(x) for x in bits if x)
    return venue,None

def slug(s): return re.sub(r"[^a-z0-9áéíóöőúüű]+","-",str(s).lower()).strip("-")
def event_id(org_id,name,start): return f"{org_id}-{slug(name)}-{slug(start)}"[:180]

def normalize(x,org,source,discovered_from=None):
    name=str(x.get("name") or "").strip(); start=x.get("startDate")
    if not name or not start: return None
    venue,address=addr_text(x.get("location"))
    return {"id":event_id(org["id"],name,start),"organizationId":org["id"],"name":name,"organizer":org["name"],
            "state":org["state"],"city":org["city"],"venue":venue,"address":address,
            "startDate":str(start),"endDate":str(x.get("endDate") or ""),
            "sourceUrl":x.get("url") or source,"discoveredFrom":discovered_from or source,
            "verifiedAt":datetime.now(timezone.utc).isoformat()}

def futureish(start):
    try:
        s=str(start).replace("Z","+00:00"); d=datetime.fromisoformat(s)
        if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
        return d>=datetime.now(timezone.utc)-timedelta(days=2)
    except Exception:return True

def links(html,base):
    host=urllib.parse.urlparse(base).netloc
    out=[]
    for href in re.findall(r'href=["\']([^"\']+)["\']',html,re.I):
        u=urllib.parse.urljoin(base,unescape(href))
        p=urllib.parse.urlparse(u)
        if p.scheme not in ("http","https") or p.netloc!=host: continue
        if u.lower().endswith(".ics") or EVENT_HINT.search(p.path+"?"+p.query):
            if u not in out: out.append(u)
    return out[:24]

def unfold_ics(text):
    lines=text.replace("\r\n","\n").replace("\r","\n").split("\n"); out=[]
    for line in lines:
        if line[:1] in (" ","\t") and out: out[-1]+=line[1:]
        else: out.append(line)
    return out

def ics_date(v):
    v=v.strip()
    for fmt in ("%Y%m%dT%H%M%SZ","%Y%m%dT%H%M%S","%Y%m%dT%H%M","%Y%m%d"):
        try:
            d=datetime.strptime(v,fmt)
            if fmt=="%Y%m%d": return d.date().isoformat()
            if v.endswith("Z"): return d.replace(tzinfo=timezone.utc).isoformat().replace("+00:00","Z")
            return d.isoformat()
        except ValueError: pass
    return v

def ics_events(text,org,source,discovered_from):
    blocks=re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT",text,re.S|re.I)
    for block in blocks:
        fields={}
        for line in unfold_ics(block):
            if ":" not in line: continue
            k,v=line.split(":",1); fields[k.split(";",1)[0].upper()]=v.strip()
        name=fields.get("SUMMARY"); start=fields.get("DTSTART")
        if not name or not start: continue
        start=ics_date(start); end=ics_date(fields.get("DTEND","")) if fields.get("DTEND") else ""
        address=fields.get("LOCATION") or None
        url=fields.get("URL") or source
        yield {"id":event_id(org["id"],name,start),"organizationId":org["id"],"name":name,"organizer":org["name"],
               "state":org["state"],"city":org["city"],"venue":None,"address":address,
               "startDate":start,"endDate":end,"sourceUrl":url,"discoveredFrom":discovered_from,
               "verifiedAt":datetime.now(timezone.utc).isoformat()}

def collect_page(url,org,root_source):
    body,ct=fetch(url); found=[]
    if ct=="text/calendar" or url.lower().endswith(".ics"):
        found.extend(ics_events(body,org,url,root_source)); return found,[],ct
    for doc in jsonld_blocks(body):
        for x in walk(doc):
            if isinstance(x,dict) and is_event(x):
                e=normalize(x,org,url,root_source)
                if e: found.append(e)
    return found,links(body,url),ct

def main():
    orgdb=json.loads(ORG_FILE.read_text(encoding="utf-8"))
    old=json.loads(EVENT_FILE.read_text(encoding="utf-8")) if EVENT_FILE.exists() else {"events":[]}
    merged={e["id"]:e for e in old.get("events",[]) if futureish(e.get("startDate"))}
    health=[]
    for org in orgdb["organizations"]:
        for source in org.get("eventSources",[]):
            row={"organizationId":org["id"],"source":source,"checkedAt":datetime.now(timezone.utc).isoformat(),
                 "status":"unknown","eventsFound":0,"pagesChecked":0}
            try:
                events,candidates,_=collect_page(source,org,source); row["pagesChecked"]=1
                for e in events:
                    if futureish(e["startDate"]): merged[e["id"]]=e
                found=sum(1 for e in events if futureish(e["startDate"]))
                for u in candidates:
                    try:
                        subevents,_,_=collect_page(u,org,source); row["pagesChecked"]+=1
                        for e in subevents:
                            if futureish(e["startDate"]):
                                merged[e["id"]]=e; found+=1
                    except Exception:
                        continue
                row["eventsFound"]=found
                row["status"]="ok-events" if found else "ok-no-structured-event"
            except Exception as ex:
                row["status"]="error"; row["error"]=str(ex)[:220]
            health.append(row)
    events=sorted(merged.values(),key=lambda e:str(e.get("startDate","")))
    now=datetime.now(timezone.utc).isoformat()
    EVENT_FILE.write_text(json.dumps({"updated":now,"events":events},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    HEALTH_FILE.write_text(json.dumps({"updated":now,"sources":health},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"organizations={len(orgdb['organizations'])} sources={len(health)} events={len(events)}")

if __name__=="__main__": main()
