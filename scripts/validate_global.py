#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
errors=[]
g=json.loads((DATA/"global.json").read_text(encoding="utf-8"))
seen=set()
if g.get("countryCodeStandard")!="ISO 3166-1 alpha-2": errors.append("unexpected country code standard")
if g.get("countryUniverseSize")!=249 or len(g.get("countries",[]))!=249: errors.append(f"expected 249 ISO country entries, got {len(g.get('countries',[]))}")
for c in g.get("countries",[]):
    iso=str(c.get("iso2",""))
    if len(iso)!=2 or iso.lower()!=iso: errors.append(f"invalid ISO2: {iso}")
    if iso in seen: errors.append(f"duplicate country: {iso}")
    if c.get("researchStatus") not in {"unresearched","researching","partial","reviewed","verified-zero"}: errors.append(f"invalid research status: {iso}")
    if c.get("route")!=f"countries/{iso}/": errors.append(f"invalid country route: {iso}")
    seen.add(iso)
    p=DATA/"countries"/iso
    if not p.is_dir(): errors.append(f"missing country data dir: {iso}"); continue
    if iso!="at":\n        org_path=p/"organizations.json"\n        if org_path.exists():\n            try: org_doc=json.loads(org_path.read_text(encoding="utf-8"))\n            except Exception as e:\n                errors.append(f"invalid country organizations JSON: {iso}: {e}")\n                org_doc={"organizations":[]}\n            ids=set()\n            for o in org_doc.get("organizations",[]):\n                oid=o.get("id")\n                if not oid: errors.append(f"missing organization id: {iso}"); continue\n                if oid in ids: errors.append(f"duplicate organization id: {iso}/{oid}")\n                ids.add(oid)\n                if o.get("country")!=iso: errors.append(f"organization country mismatch: {iso}/{oid}")\n                if not o.get("website"): errors.append(f"missing official website: {iso}/{oid}")\n                if not o.get("city"): errors.append(f"missing verified city: {iso}/{oid}")\n                ev=o.get("evidenceSources") or []\n                if not any(e.get("type")=="official" and e.get("url") for e in ev): errors.append(f"missing official evidence: {iso}/{oid}")\n                profile=ROOT/"countries"/iso/"organizations"/f"{oid}.html"\n                if not profile.exists(): errors.append(f"missing generated profile: {iso}/{oid}")\n            expected_count=sum(1 for o in org_doc.get("organizations",[]) if o.get("entityClass")!="activity")\n            if c.get("counts",{}).get("organizations")!=expected_count: errors.append(f"stale derived country organization count: {iso}")\n    if iso=="at":
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
