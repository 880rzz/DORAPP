#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
orgdb=json.loads((ROOT/"data/organizations.json").read_text(encoding="utf-8"))
evdb=json.loads((ROOT/"data/events.json").read_text(encoding="utf-8"))
states={s["id"] for s in orgdb["states"]}
orgs=orgdb["organizations"]
ids=[o["id"] for o in orgs]
errors=[]
if len(ids)!=len(set(ids)): errors.append("duplicate organization id")
for o in orgs:
    if o.get("state") not in states: errors.append(f"unknown state: {o.get('id')} -> {o.get('state')}")
    if not o.get("name") or not o.get("city") or not o.get("intro"): errors.append(f"incomplete organization: {o.get('id')}")
    for key in ("website","facebook","instagram"):
        u=o.get(key)
        if u and not str(u).startswith(("https://","http://")): errors.append(f"invalid {key}: {o.get('id')} -> {u}")
    for u in o.get("eventSources",[]):
        if not str(u).startswith(("https://","http://")): errors.append(f"invalid event source: {o.get('id')} -> {u}")
orgset=set(ids)
eventids=[]
for e in evdb.get("events",[]):
    eventids.append(e.get("id"))
    if e.get("organizationId") not in orgset: errors.append(f"orphan event: {e.get('id')}")
    if not e.get("name") or not e.get("startDate") or not e.get("sourceUrl"): errors.append(f"incomplete event: {e.get('id')}")
if len(eventids)!=len(set(eventids)): errors.append("duplicate event id")
print(f"states={len(states)} organizations={len(orgs)} events={len(eventids)}")
if errors:
    print("\n".join("ERROR: "+x for x in errors))
    sys.exit(1)
