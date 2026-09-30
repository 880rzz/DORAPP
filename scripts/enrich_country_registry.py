#!/usr/bin/env python3
import json
from pathlib import Path
import pycountry

ROOT=Path(__file__).resolve().parents[1]
GLOBAL=ROOT/"data"/"global.json"

def main():
    g=json.loads(GLOBAL.read_text(encoding="utf-8"))
    changed=0
    for c in g.get("countries",[]):
        iso=str(c.get("iso2","")).upper()
        x=pycountry.countries.get(alpha_2=iso)
        if not x:
            continue
        n=c.setdefault("name",{})
        common=getattr(x,"common_name",None) or x.name
        official=getattr(x,"official_name",None)
        if common and n.get("en")!=common:
            n["en"]=common
            changed+=1
        if official:
            n["officialEn"]=official
        c["iso3"]=x.alpha_3
    GLOBAL.write_text(json.dumps(g,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Country metadata enriched from ISO registry; changed names={changed}")

if __name__=="__main__":
    main()
