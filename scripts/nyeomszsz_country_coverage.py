#!/usr/bin/env python3
"""Validate NYEOMSZSZ country coverage assessment artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COVERAGE_DIR = ROOT / "data" / "nyeomszsz" / "coverage"
SCHEMA = COVERAGE_DIR / "checklist-schema.json"


def validate_file(path: Path, schema: dict) -> list[str]:
    errors: list[str] = []
    doc = json.loads(path.read_text(encoding="utf-8"))
    required = set(schema["requiredSourceClasses"])
    allowed = set(schema["allowedCoverageStatuses"])
    if doc.get("countryComplete") is True:
        errors.append(f"{path.name}: countryComplete=true is forbidden without full closure evidence")
    if doc.get("coverageStatus") == "complete":
        errors.append(f"{path.name}: coverageStatus=complete forbidden in pilot artifacts")
    checklist = doc.get("sourceChecklist") or []
    classes = {row.get("class") for row in checklist}
    missing = required - classes
    if missing:
        errors.append(f"{path.name}: missing source classes {sorted(missing)}")
    for row in checklist:
        if row.get("status") not in allowed:
            errors.append(f"{path.name}: invalid status {row.get('status')} for {row.get('class')}")
    seed = doc.get("umbrellaSeed") or {}
    if seed.get("lifecycle") not in {None, "DISCOVERED", "DISPUTED", "NEEDS_REVIEW"}:
        errors.append(f"{path.name}: umbrella seed lifecycle advanced unexpectedly to {seed.get('lifecycle')}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, default=COVERAGE_DIR)
    args = parser.parse_args(argv)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors: list[str] = []
    files = sorted(p for p in args.dir.glob("*.json") if p.name != "checklist-schema.json")
    if not files:
        errors.append("no coverage assessment files found")
    for path in files:
        errors.extend(validate_file(path, schema))
    if errors:
        print("Coverage validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Coverage validation OK: {len(files)} assessed countries; none marked complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
