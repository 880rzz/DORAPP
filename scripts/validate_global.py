#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
errors=[]
g=json.loads((DATA/"global.json").read_text(encoding="utf-8"))
seen=set()
for c in g.get("countries",[]):
    iso=str(c.get("iso2",""))
    if len(iso)!=2 or iso.lower()!=iso: errors.append(f"invalid ISO2: {iso}")
    if iso in seen: errors.append(f"duplicate country: {iso}")
    seen.add(iso)
    p=DATA/"countries"/iso
    if not p.is_dir(): errors.append(f"missing country data dir: {iso}"); continue
    if iso=="at":
        org=json.loads((DATA/"organizations.json").read_text(encoding="utf-8"))
        ev=json.loads((DATA/"events.json").read_text(encoding="utf-8"))
        edu=json.loads((DATA/"education.json").read_text(encoding="utf-8"))
        entity=len(org.get("organizations",[]))
        organizations=sum(1 for o in org.get("organizations",[]) if o.get("entityClass")!="activity")
        activity=entity-organizations
        events=len(ev.get("events",[]))
        education=len(edu.get("institutions",edu.get("education",edu.get("items",[]))))
        expected={"organizations":organizations,"activities":activity,"entities":entity,"events":events,"education":education}
        if c.get("counts")!=expected: errors.append(f"stale derived counts for at: {c.get('counts')} != {expected}")
        for name in ("organizations.json","events.json","education.json","source-health.json","articles.json","discovery-sources.json"):
            legacy=DATA/name
            mirror=p/name
            if legacy.exists() and (not mirror.exists() or legacy.read_bytes()!=mirror.read_bytes()):
                errors.append(f"Austria compatibility mirror drift: {name}")
if errors:
    print("\n".join("ERROR: "+x for x in errors));sys.exit(1)
print(f"Global directory validation OK: {len(seen)} country registry entries")
