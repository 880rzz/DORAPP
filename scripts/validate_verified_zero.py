#!/usr/bin/env python3
"""Validate that verified-zero is an evidence-backed terminal research state."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
g=json.loads((DATA/"global.json").read_text(encoding="utf-8"))
errors=[]
required_categories={"organizations","education","media","religious","scouting","cultural","events","historical"}

for c in g.get("countries",[]):
    if c.get("researchStatus")!="verified-zero":
        continue
    iso=c["iso2"]
    p=DATA/"countries"/iso
    comp_path=p/"research-completion.json"
    if not comp_path.exists():
        errors.append(f"{iso}: verified-zero missing research-completion.json")
        continue
    comp=json.loads(comp_path.read_text(encoding="utf-8"))
    if comp.get("country")!=iso or comp.get("status")!="verified-zero":
        errors.append(f"{iso}: completion identity/status mismatch")
    if comp.get("canonicalOrganizationIds"):
        errors.append(f"{iso}: verified-zero has canonical organizations")
    if comp.get("canonicalEducationIds"):
        errors.append(f"{iso}: verified-zero has canonical education")
    coverage=comp.get("coverage") or []
    categories={str(x.get("category")) for x in coverage if str(x.get("status","")).startswith("reviewed")}
    missing=sorted(required_categories-categories)
    if missing:
        errors.append(f"{iso}: missing reviewed coverage: {','.join(missing)}")
    evidence=comp.get("negativeEvidence") or {}
    if not evidence.get("checkedAt") or not evidence.get("nextReviewAt"):
        errors.append(f"{iso}: negative evidence dates missing")
    if len(evidence.get("sources") or [])<2:
        errors.append(f"{iso}: fewer than two negative-evidence sources")
    if not evidence.get("queryScope"):
        errors.append(f"{iso}: negative evidence queryScope missing")
    if not evidence.get("method"):
        errors.append(f"{iso}: negative evidence method missing")

if errors:
    print("\n".join("ERROR: "+e for e in errors))
    raise SystemExit(1)
print("verified-zero evidence gate: OK")
