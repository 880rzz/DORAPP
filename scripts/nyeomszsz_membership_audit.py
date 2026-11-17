#!/usr/bin/env python3
"""Validate NYEOMSZSZ membership reconciliation artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECON_PATH = ROOT / "data" / "nyeomszsz" / "membership-source-reconciliation.json"
SEEDS_PATH = ROOT / "data" / "nyeomszsz" / "discovery-seeds.json"
TARGET_ISO2 = {
    "AT",
    "BA",
    "CH",
    "CZ",
    "DE",
    "EE",
    "ES",
    "FI",
    "FR",
    "GB",
    "IE",
    "IT",
    "LT",
    "LV",
    "MK",
    "NL",
    "NO",
    "PL",
    "PT",
    "SE",
}
ALLOWED_STATUS = {"current-candidate", "disputed", "unknown", "historical", "rejected"}
HOMEPAGE_17 = {
    "SE",
    "NO",
    "FI",
    "LV",
    "EE",
    "LT",
    "PL",
    "CZ",
    "GB",
    "NL",
    "FR",
    "PT",
    "ES",
    "IT",
    "CH",
    "DE",
    "AT",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(recon: dict, seeds: dict) -> list[str]:
    errors: list[str] = []
    entries = recon.get("directoryEntries") or []
    if len(entries) != 20:
        errors.append(f"expected 20 directory entries, found {len(entries)}")
    homepage = recon.get("homepageMemberCountries") or []
    if len(homepage) != 17:
        errors.append(f"expected 17 homepage countries, found {len(homepage)}")

    homepage_iso = {row.get("iso2Primary") for row in homepage}
    if homepage_iso != HOMEPAGE_17:
        errors.append(f"homepage ISO set mismatch: {sorted(homepage_iso)}")

    conflict = set(recon.get("sourceConflictSummary", {}).get("directoryOnlyRelativeToHomepageCountryList") or [])
    if conflict != {"BA", "IE", "MK"}:
        errors.append(f"expected directory-only conflict BA/IE/MK, found {sorted(conflict)}")

    seed_by_id = {row["seedId"]: row for row in seeds.get("seeds") or []}
    if len(seed_by_id) != 20:
        errors.append(f"expected 20 discovery seeds, found {len(seed_by_id)}")

    seen_iso = set()
    for entry in entries:
        seed_id = entry.get("seedId")
        status = entry.get("memberStatusEvidence")
        iso_list = entry.get("operationalCountryIso2") or []
        if status not in ALLOWED_STATUS:
            errors.append(f"{seed_id}: invalid memberStatusEvidence {status}")
        if not iso_list:
            errors.append(f"{seed_id}: missing operationalCountryIso2")
        else:
            iso = iso_list[0]
            seen_iso.add(iso)
            if iso not in TARGET_ISO2:
                errors.append(f"{seed_id}: iso {iso} outside Issue #59 research scope")
        if seed_id not in seed_by_id:
            errors.append(f"{seed_id}: missing discovery seed")
        else:
            seed = seed_by_id[seed_id]
            if seed.get("lifecycle") != "DISCOVERED":
                errors.append(f"{seed_id}: seed lifecycle must remain DISCOVERED in audit PR")
            if seed.get("memberStatusEvidence") != status:
                errors.append(f"{seed_id}: seed/reconciliation status mismatch")
        # Directory listing alone is never publishable.
        if entry.get("dorappLifecycle") not in {"DISCOVERED", "DISPUTED", "NEEDS_REVIEW"}:
            errors.append(f"{seed_id}: audit lifecycle unexpectedly advanced to {entry.get('dorappLifecycle')}")

        if entry.get("homepageMembershipClaim") == "absent-from-homepage-17" and status != "disputed":
            errors.append(f"{seed_id}: homepage-absent entries must be disputed until independently verified")

    missing = TARGET_ISO2 - seen_iso
    if missing:
        errors.append(f"research scope countries missing from directory seeds: {sorted(missing)}")

    # Jurisdiction safety checks
    gb = next(e for e in entries if e["seedId"] == "nyeomszsz-dir-gb-maosz")
    if "United Kingdom" in json.dumps(gb.get("operationalCountryIso2")):
        errors.append("GB seed must not encode United Kingdom as automatic operational ISO identity")
    ie = next(e for e in entries if e["seedId"] == "nyeomszsz-dir-ie-island")
    notes = json.dumps(ie.get("jurisdictionNotes") or "")
    if "Northern Ireland" not in notes:
        errors.append("IE seed must explicitly warn against Northern Ireland inference")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recon", type=Path, default=RECON_PATH)
    parser.add_argument("--seeds", type=Path, default=SEEDS_PATH)
    args = parser.parse_args(argv)
    errors = validate(load(args.recon), load(args.seeds))
    if errors:
        print("NYEOMSZSZ membership audit FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("NYEOMSZSZ membership audit OK: 17 homepage vs 20 directory conflict documented; seeds remain DISCOVERED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
