#!/usr/bin/env python3
from __future__ import annotations
import json,re,urllib.request,urllib.parse
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from datetime import datetime,timezone,timedelta
from html import unescape

ROOT=Path(__file__).resolve().parents[1]
ORG_FILE=ROOT/"data/organizations.json"
EVENT_FILE=ROOT/"data/events.json"
HEALTH_FILE=ROOT/"data/source-health.json"
UA="DORAPP-AustriaHungarianPrograms/1.2 (+https://github.com/880rzz/DORAPP)"
EVENT_HINT=re.compile(r"(event|events|event-details|veranstaltung|termine|program|programme|esemeny|rendezveny|calendar)",re.I)

def fetch(url:str)->tuple[str,str]:
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml,text/calendar,application/json;q=0.9,*/*;q=0.8"})
    with urllib.request.urlopen(req,timeout=8) as r:
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

def text_value(v):
    if isinstance(v,str): return clean_text(v)
    if isinstance(v,dict): return clean_text(v.get("name") or v.get("description") or "")
    return ""

def clean_text(v):
    return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",unescape(str(v or "")))).strip()

def offer_details(v):
    offers=v if isinstance(v,list) else ([v] if isinstance(v,dict) else [])
    for o in offers:
        if not isinstance(o,dict): continue
        url=o.get("url")
        price=o.get("price")
        currency=o.get("priceCurrency")
        availability=o.get("availability")
        if url or price is not None or currency or availability:
            return url,price,currency,availability
    return None,None,None,None

def people_names(v):
    vals=v if isinstance(v,list) else ([v] if v else [])
    out=[]
    for p in vals:
        name=text_value(p)
        if name and name not in out: out.append(name)
    return out

def normalize(x,org,source,discovered_from=None):
    name=str(x.get("name") or "").strip(); start=x.get("startDate")
    if not name or not start: return None
    venue,address=addr_text(x.get("location"))
    registration,price,currency,availability=offer_details(x.get("offers"))
    image=x.get("image")
    if isinstance(image,list): image=image[0] if image else None
    if isinstance(image,dict): image=image.get("url")
    audience=x.get("audience")
    audience_text=text_value(audience)
    return {"id":event_id(org["id"],name,start),"organizationId":org["id"],"name":name,"organizer":org["name"],
            "state":org["state"],"city":org["city"],"venue":venue,"address":address,
            "startDate":str(start),"endDate":str(x.get("endDate") or ""),
            "description":clean_text(x.get("description")),
            "eventStatus":text_value(x.get("eventStatus")) or None,
            "attendanceMode":text_value(x.get("eventAttendanceMode")) or None,
            "registrationUrl":registration,
            "price":price,"priceCurrency":currency,"availability":availability,
            "performers":people_names(x.get("performer") or x.get("performers")),
            "audience":audience_text or None,"image":image,
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
    return out[:6]

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
               "startDate":start,"endDate":end,"description":clean_text(fields.get("DESCRIPTION","")),
               "registrationUrl":None,"price":None,"priceCurrency":None,"availability":None,
               "performers":[],"audience":None,"image":None,"eventStatus":None,"attendanceMode":None,
               "sourceUrl":url,"discoveredFrom":discovered_from,
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
    def audit_source(org,source):
        row={"organizationId":org["id"],"source":source,"checkedAt":datetime.now(timezone.utc).isoformat(),
             "status":"unknown","eventsFound":0,"pagesChecked":0}
        collected=[]
        try:
            events,candidates,_=collect_page(source,org,source); row["pagesChecked"]=1
            collected.extend(e for e in events if futureish(e["startDate"]))
            for u in candidates:
                try:
                    subevents,_,_=collect_page(u,org,source); row["pagesChecked"]+=1
                    collected.extend(e for e in subevents if futureish(e["startDate"]))
                except Exception:
                    continue
            unique={e["id"]:e for e in collected}
            collected=list(unique.values())
            row["eventsFound"]=len(collected)
            row["status"]="ok-events" if collected else "ok-no-structured-event"
        except Exception as ex:
            row["status"]="error"; row["error"]=str(ex)[:220]
        return row,collected

    jobs=[(org,source) for org in orgdb["organizations"] for source in org.get("eventSources",[])]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures=[pool.submit(audit_source,org,source) for org,source in jobs]
        for future in as_completed(futures):
            row,collected=future.result()
            health.append(row)
            for e in collected:
                merged[e["id"]]=e
    health.sort(key=lambda x:(x["organizationId"],x["source"]))
    events=sorted(merged.values(),key=lambda e:str(e.get("startDate","")))
    now=datetime.now(timezone.utc).isoformat()
    EVENT_FILE.write_text(json.dumps({"updated":now,"events":events},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    HEALTH_FILE.write_text(json.dumps({"updated":now,"sources":health},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"organizations={len(orgdb['organizations'])} sources={len(health)} events={len(events)}")

if __name__=="__main__": main()
