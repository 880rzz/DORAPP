#!/usr/bin/env python3
import json, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GLOBAL=ROOT/"data"/"global.json"
URL="https://restcountries.com/v3.1/all?fields=cca2,cca3,name,translations,altSpellings,region,subregion"

def fetch():
    req=urllib.request.Request(URL,headers={"User-Agent":"DORAPP-Global-Steward/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def main():
    g=json.loads(GLOBAL.read_text(encoding="utf-8"))
    rows=fetch()
    by={str(x.get("cca2","")).lower():x for x in rows if x.get("cca2")}
    changed=0
    for c in g.get("countries",[]):
        x=by.get(c.get("iso2"))
        if not x:
            continue
        n=c.setdefault("name",{})
        common=(x.get("name") or {}).get("common")
        official=(x.get("name") or {}).get("official")
        hu=((x.get("translations") or {}).get("hun") or {}).get("common")
        if common and n.get("en")!=common:
            n["en"]=common; changed+=1
        if hu and n.get("hu")!=hu:
            n["hu"]=hu; changed+=1
        if official:
            n["officialEn"]=official
        if x.get("cca3"):
            c["iso3"]=x["cca3"]
        if x.get("region"):
            c["worldRegion"]=x["region"]
        if x.get("subregion"):
            c["worldSubregion"]=x["subregion"]
        alts=[a for a in x.get("altSpellings",[]) if isinstance(a,str) and a.strip()]
        if alts:
            c["aliases"]=sorted(set(alts))
    GLOBAL.write_text(json.dumps(g,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Country metadata enriched; changed names={changed}")

if __name__=="__main__":
    main()
