#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
orgdb=json.loads((ROOT/"data/organizations.json").read_text(encoding="utf-8"))
evdb=json.loads((ROOT/"data/events.json").read_text(encoding="utf-8"))
edudb=json.loads((ROOT/"data/education.json").read_text(encoding="utf-8"))
states={s["id"] for s in orgdb["states"]}
orgs=orgdb["organizations"]
ids=[o["id"] for o in orgs]
errors=[]
umbrella_ids={u.get("id") for u in orgdb.get("umbrellaOrganizations",[])}
network_ids={n.get("id") for n in orgdb.get("regionalNetworks",[])}
if len(ids)!=len(set(ids)): errors.append("duplicate organization id")
for o in orgs:
    if o.get("state") not in states: errors.append(f"unknown state: {o.get('id')} -> {o.get('state')}")
    if not o.get("name") or not o.get("city") or not o.get("intro"): errors.append(f"incomplete organization: {o.get('id')}")
    for m in o.get("memberships",[]):
        if m.get("umbrellaId") not in umbrella_ids:
            errors.append(f"unknown umbrella membership: {o.get('id')} -> {m.get('umbrellaId')}")
        if not str(m.get("sourceUrl","")).startswith(("http://","https://")):
            errors.append(f"invalid membership source: {o.get('id')}")
    for n in o.get("regionalNetworks",[]):
        if n.get("networkId") not in network_ids:
            errors.append(f"unknown regional network: {o.get('id')} -> {n.get('networkId')}")
        if not str(n.get("sourceUrl","")).startswith(("http://","https://")):
            errors.append(f"invalid regional network source: {o.get('id')}")
    for key in ("website","facebook","instagram"):
        u=o.get(key)
        if u and not str(u).startswith(("https://","http://")): errors.append(f"invalid {key}: {o.get('id')} -> {u}")
    for u in o.get("eventSources",[]):
        if not str(u).startswith(("https://","http://")): errors.append(f"invalid event source: {o.get('id')} -> {u}")
    history=o.get("history") or {}
    if history and not isinstance(history,dict):
        errors.append(f"invalid history object: {o.get('id')}")
    elif history:
        if history.get("summary") is not None and not isinstance(history.get("summary"),str):
            errors.append(f"invalid history summary: {o.get('id')}")
        milestones=history.get("milestones") or []
        if not isinstance(milestones,list):
            errors.append(f"invalid history milestones: {o.get('id')}")
        else:
            for m in milestones:
                if not isinstance(m,dict):
                    errors.append(f"invalid milestone: {o.get('id')}")
                    continue
                su=m.get("sourceUrl")
                if su and not str(su).startswith(("https://","http://")):
                    errors.append(f"invalid milestone source: {o.get('id')} -> {su}")
    for key in ("activities","targetGroups","languages"):
        value=o.get(key)
        if value is not None and (not isinstance(value,list) or any(not isinstance(x,str) or not x.strip() for x in value)):
            errors.append(f"invalid {key}: {o.get('id')}")
    if o.get("profileVerifiedAt") is not None and not isinstance(o.get("profileVerifiedAt"),str):
        errors.append(f"invalid profileVerifiedAt: {o.get('id')}")
orgset=set(ids)
eventids=[]
for e in evdb.get("events",[]):
    eventids.append(e.get("id"))
    if e.get("organizationId") not in orgset: errors.append(f"orphan event: {e.get('id')}")
    if not e.get("name") or not e.get("startDate") or not e.get("sourceUrl"): errors.append(f"incomplete event: {e.get('id')}")
if len(eventids)!=len(set(eventids)): errors.append("duplicate event id")
edu_ids=[]
valid_levels={"nursery","kindergarten","primary","secondary","tertiary","adult"}
for x in edudb.get("institutions",[]):
    edu_ids.append(x.get("id"))
    if x.get("state") not in states: errors.append(f"unknown education state: {x.get('id')} -> {x.get('state')}")
    if not x.get("name") or not x.get("city") or not x.get("summary") or not x.get("sourceUrl"):
        errors.append(f"incomplete education record: {x.get('id')}")
    levels=x.get("level") or []
    if not levels or any(level not in valid_levels for level in levels):
        errors.append(f"invalid education level: {x.get('id')} -> {levels}")
    for key in ("website","sourceUrl"):
        u=x.get(key)
        if u and not str(u).startswith(("https://","http://")):
            errors.append(f"invalid education {key}: {x.get('id')} -> {u}")
if len(edu_ids)!=len(set(edu_ids)): errors.append("duplicate education id")
print(f"states={len(states)} organizations={len(orgs)} events={len(eventids)} education={len(edu_ids)}")
if errors:
    print("\n".join("ERROR: "+x for x in errors))
    sys.exit(1)
