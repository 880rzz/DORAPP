#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
errors=[]

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"invalid JSON: {path}: {e}")
        return {}

g=read_json(DATA/"global.json")
seen=set()

if g.get("countryCodeStandard")!="ISO 3166-1 alpha-2":
    errors.append("unexpected country code standard")
if g.get("countryUniverseSize")!=249 or len(g.get("countries",[]))!=249:
    errors.append(f"expected 249 ISO country entries, got {len(g.get('countries',[]))}")

for c in g.get("countries",[]):
    iso=str(c.get("iso2",""))
    if len(iso)!=2 or iso.lower()!=iso:
        errors.append(f"invalid ISO2: {iso}")
    if iso in seen:
        errors.append(f"duplicate country: {iso}")
    seen.add(iso)

    if c.get("researchStatus") not in {"unresearched","researching","partial","reviewed","verified-zero"}:
        errors.append(f"invalid research status: {iso}")
    if c.get("route")!=f"countries/{iso}/":
        errors.append(f"invalid country route: {iso}")

    p=DATA/"countries"/iso
    if not p.is_dir():
        errors.append(f"missing country data dir: {iso}")
        continue

    if iso!="at":
        org_path=p/"organizations.json"
        if org_path.exists():
            org_doc=read_json(org_path)
            ids=set()
            for o in org_doc.get("organizations",[]):
                oid=o.get("id")
                if not oid:
                    errors.append(f"missing organization id: {iso}")
                    continue
                if oid in ids:
                    errors.append(f"duplicate organization id: {iso}/{oid}")
                ids.add(oid)

                if o.get("country")!=iso:
                    errors.append(f"organization country mismatch: {iso}/{oid}")
                if not o.get("website"):
                    errors.append(f"missing official website: {iso}/{oid}")
                if not o.get("city"):
                    errors.append(f"missing verified city: {iso}/{oid}")

                evidence=o.get("evidenceSources") or []
                if not any(e.get("type")=="official" and e.get("url") for e in evidence):
                    errors.append(f"missing official evidence: {iso}/{oid}")

                profile=ROOT/"countries"/iso/"organizations"/f"{oid}.html"
                if not profile.exists():
                    errors.append(f"missing generated profile: {iso}/{oid}")

            expected_count=sum(
                1 for o in org_doc.get("organizations",[])
                if o.get("entityClass")!="activity"
            )
            actual_count=c.get("counts",{}).get("organizations")
            if actual_count!=expected_count:
                errors.append(
                    f"stale derived country organization count: {iso}: "
                    f"{actual_count} != {expected_count}"
                )
        elif c.get("counts",{}).get("organizations",0)!=0:
            errors.append(f"country count without organizations.json: {iso}")

    if iso=="at":
        org=read_json(DATA/"organizations.json")
        ev=read_json(DATA/"events.json")
        edu=read_json(DATA/"education.json")
        entity=len(org.get("organizations",[]))
        organizations=sum(
            1 for o in org.get("organizations",[])
            if o.get("entityClass")!="activity"
        )
        activity=entity-organizations
        events=len(ev.get("events",[]))
        education=len(edu.get("institutions",edu.get("education",edu.get("items",[]))))
        expected={
            "organizations":organizations,
            "activities":activity,
            "entities":entity,
            "events":events,
            "education":education,
        }
        if c.get("counts")!=expected:
            errors.append(f"stale derived counts for at: {c.get('counts')} != {expected}")

        for name in (
            "organizations.json","events.json","education.json",
            "source-health.json","articles.json","discovery-sources.json"
        ):
            legacy=DATA/name
            mirror=p/name
            if legacy.exists() and (
                not mirror.exists() or legacy.read_bytes()!=mirror.read_bytes()
            ):
                errors.append(f"Austria compatibility mirror drift: {name}")

if errors:
    print("\n".join("ERROR: "+x for x in errors))
    sys.exit(1)

print(f"Global directory validation OK: {len(seen)} country registry entries")
