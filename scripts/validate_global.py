#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
errors=[]

TRUSTED_EVIDENCE={"official","government","institutional","registry","first-party-person"}

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"invalid JSON: {path}: {e}")
        return {}

def validate_completion(iso,p,c):
    completion_path=p/"research-completion.json"
    if c.get("researchStatus")=="reviewed":
        if not completion_path.exists():
            errors.append(f"reviewed country missing research-completion.json: {iso}")
            return
        comp=read_json(completion_path)
        if comp.get("country")!=iso:
            errors.append(f"completion country mismatch: {iso}")
        if comp.get("status")!="reviewed":
            errors.append(f"completion status not reviewed: {iso}")
        unresolved=comp.get("unresolvedStrongCandidates") or []
        if unresolved:
            errors.append(f"reviewed country has unresolved strong candidates: {iso}")
        coverage=comp.get("coverage") or []
        if not coverage:
            errors.append(f"reviewed country missing coverage matrix: {iso}")
        for row in coverage:
            if not str(row.get("status","")).startswith("reviewed"):
                errors.append(f"incomplete research coverage: {iso}/{row.get('category')}")

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

    validate_completion(iso,p,c)

    if iso!="at":
        org_path=p/"organizations.json"
        org_doc={"organizations":[]}
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
                if not o.get("city") and o.get("scope")!="national":
                    errors.append(f"missing verified city or national scope: {iso}/{oid}")

                evidence=o.get("evidenceSources") or []
                trusted=[e for e in evidence if e.get("type") in TRUSTED_EVIDENCE and e.get("url")]
                if not trusted:
                    errors.append(f"missing trusted evidence: {iso}/{oid}")
                if not o.get("website") and len(trusted)<2:
                    errors.append(f"no official website and insufficient corroboration: {iso}/{oid}")

                profile=ROOT/"countries"/iso/"organizations"/f"{oid}.html"
                if not profile.exists():
                    errors.append(f"missing generated profile: {iso}/{oid}")

        elif c.get("counts",{}).get("organizations",0)!=0:
            errors.append(f"country count without organizations.json: {iso}")

        edu_path=p/"education.json"
        edu_doc=read_json(edu_path) if edu_path.exists() else {"institutions":[]}

        org_items=org_doc.get("organizations",[])
        expected={
            "organizations":sum(1 for o in org_items if o.get("entityClass")!="activity"),
            "activities":sum(1 for o in org_items if o.get("entityClass")=="activity"),
            "entities":len(org_items),
            "events":0,
            "education":len(edu_doc.get("institutions",edu_doc.get("education",edu_doc.get("items",[]))))
        }
        event_path=p/"events.json"
        if event_path.exists():
            ev=read_json(event_path)
            expected["events"]=len(ev.get("events",ev.get("items",[])))

        if c.get("counts")!=expected:
            errors.append(f"stale derived counts for {iso}: {c.get('counts')} != {expected}")

    if iso=="at":
        org=read_json(DATA/"organizations.json")
        ev=read_json(DATA/"events.json")
        edu=read_json(DATA/"education.json")
        entity=len(org.get("organizations",[]))
        organizations=sum(1 for o in org.get("organizations",[]) if o.get("entityClass")!="activity")
        activity=entity-organizations
        events=len(ev.get("events",[]))
        education=len(edu.get("institutions",edu.get("education",edu.get("items",[]))))
        expected={"organizations":organizations,"activities":activity,"entities":entity,"events":events,"education":education}
        if c.get("counts")!=expected:
            errors.append(f"stale derived counts for at: {c.get('counts')} != {expected}")

        for name in ("organizations.json","events.json","education.json","source-health.json","articles.json","discovery-sources.json"):
            legacy=DATA/name
            mirror=p/name
            if legacy.exists() and (not mirror.exists() or legacy.read_bytes()!=mirror.read_bytes()):
                errors.append(f"Austria compatibility mirror drift: {name}")

if errors:
    print("\n".join("ERROR: "+x for x in errors))
    sys.exit(1)

print(f"Global directory validation OK: {len(seen)} country registry entries")
