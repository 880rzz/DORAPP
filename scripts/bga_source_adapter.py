#!/usr/bin/env python3
"""Lawful Bethlen Gábor Alapkezelő (BGA) source adapter.

Default mode is BLOCKED_LICENSE_OR_EXPORT. This module never scrapes the
JSF map UI and never treats grant records as NYEOMSZSZ membership or
verified organizational activity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATUS_PATH = ROOT / "data" / "bga" / "import-status.json"
BLOCKED = "BLOCKED_LICENSE_OR_EXPORT"
MODES = ("official_api", "approved_file_import", "BLOCKED_LICENSE_OR_EXPORT")


@dataclass
class BgaApplicant:
    applicantId: str
    legalName: str
    applicantType: str | None = None
    taxIdRedacted: bool = True
    sourceRefs: list[str] = field(default_factory=list)


@dataclass
class GrantApplication:
    applicationId: str
    applicantId: str
    programmeCode: str | None = None
    submittedAt: str | None = None
    sourceRefs: list[str] = field(default_factory=list)


@dataclass
class GrantDecision:
    decisionId: str
    applicationId: str
    outcome: str
    decidedAt: str | None = None
    sourceRefs: list[str] = field(default_factory=list)


@dataclass
class GrantAward:
    awardId: str
    applicationId: str
    amount: float | None = None
    currency: str | None = None
    sourceRefs: list[str] = field(default_factory=list)


@dataclass
class OrganizationCandidate:
    candidateId: str
    displayName: str
    matchedApplicantId: str | None = None
    matchConfidence: str = "unmatched"
    notes: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize one steward-approved import row into separated concepts."""
    applicant_id = str(raw.get("applicantId") or raw.get("applicant_id") or "").strip()
    legal_name = str(raw.get("legalName") or raw.get("applicantName") or "").strip()
    application_id = str(raw.get("applicationId") or raw.get("application_id") or "").strip()
    outcome = str(raw.get("outcome") or raw.get("decision") or "unknown").strip().lower()
    if not applicant_id or not legal_name or not application_id:
        raise ValueError("approved import rows require applicantId, legalName, applicationId")

    # Never retain raw tax identifiers in normalized public-bound structures.
    if raw.get("taxId") or raw.get("adoszam") or raw.get("taxNumber"):
        tax_redacted = True
    else:
        tax_redacted = True

    applicant = BgaApplicant(applicantId=applicant_id, legalName=legal_name, taxIdRedacted=tax_redacted)
    application = GrantApplication(
        applicationId=application_id,
        applicantId=applicant_id,
        programmeCode=raw.get("programmeCode") or raw.get("construction"),
        submittedAt=raw.get("submittedAt"),
    )
    decision = GrantDecision(
        decisionId=str(raw.get("decisionId") or f"decision:{application_id}"),
        applicationId=application_id,
        outcome=outcome,
        decidedAt=raw.get("decidedAt"),
    )
    award = None
    if outcome in {"awarded", "supported", "tamogatott", "successful"}:
        award = GrantAward(
            awardId=str(raw.get("awardId") or f"award:{application_id}"),
            applicationId=application_id,
            amount=raw.get("amount"),
            currency=raw.get("currency") or "HUF",
        )
    candidate = OrganizationCandidate(
        candidateId=f"bga-candidate:{applicant_id}",
        displayName=legal_name,
        matchedApplicantId=applicant_id,
        matchConfidence="name-only-unverified",
        notes="Grant-linked applicant is not proof of NYEOMSZSZ membership or ongoing activity.",
    )
    return {
        "applicant": asdict(applicant),
        "application": asdict(application),
        "decision": asdict(decision),
        "award": asdict(award) if award else None,
        "unsuccessfulApplication": None
        if award
        else {
            "applicationId": application_id,
            "outcome": outcome,
        },
        "organizationCandidate": asdict(candidate),
    }


def load_approved_file(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        rows = payload.get("records") or payload.get("items") or []
    else:
        rows = payload
    if not isinstance(rows, list):
        raise ValueError("approved file must contain a list or {records|items: []}")
    return [normalize_record(row) for row in rows]


def write_status(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def blocked_status(reason: str) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "asOf": utc_now(),
        "mode": BLOCKED,
        "ingestAllowed": False,
        "blockerId": BLOCKED,
        "reason": reason,
        "requiredAccess": [
            "Documented bulk API or official export",
            "Explicit reuse terms for public-interest directory linking",
            "Guidance forbidding republication of tax IDs / personal applicants",
        ],
        "robots": "https://adattar.bgazrt.hu/robots.txt Disallow: /",
        "ui": "https://adattar.bgazrt.hu/adattar/riport/terkep.xhtml",
        "counts": {
            "applicants": 0,
            "applications": 0,
            "awards": 0,
            "unsuccessful": 0,
            "organizationCandidates": 0,
        },
    }


def summarize(records: Iterable[dict[str, Any]]) -> dict[str, int]:
    applicants = set()
    applications = set()
    awards = 0
    unsuccessful = 0
    candidates = set()
    for row in records:
        applicants.add(row["applicant"]["applicantId"])
        applications.add(row["application"]["applicationId"])
        if row.get("award"):
            awards += 1
        if row.get("unsuccessfulApplication"):
            unsuccessful += 1
        candidates.add(row["organizationCandidate"]["candidateId"])
    return {
        "applicants": len(applicants),
        "applications": len(applications),
        "awards": awards,
        "unsuccessful": unsuccessful,
        "organizationCandidates": len(candidates),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, default=BLOCKED)
    parser.add_argument("--input", type=Path, help="Steward-approved import file for approved_file_import mode")
    parser.add_argument("--status-out", type=Path, default=DEFAULT_STATUS_PATH)
    parser.add_argument("--normalized-out", type=Path, help="Optional normalized JSON output path")
    args = parser.parse_args(argv)

    if args.mode == "official_api":
        status = blocked_status(
            "official_api mode selected, but no authorized BGA bulk API/export endpoint is configured."
        )
        status["mode"] = "official_api"
        write_status(args.status_out, status)
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 2

    if args.mode == BLOCKED:
        status = blocked_status(
            "No authorized bulk channel evidenced; refusing live JSF scrape per Issue #59 and robots.txt."
        )
        write_status(args.status_out, status)
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0

    if not args.input:
        print("approved_file_import requires --input", file=sys.stderr)
        return 2
    records = load_approved_file(args.input)
    checksum = sha256_file(args.input)
    status = {
        "schemaVersion": 1,
        "asOf": utc_now(),
        "mode": "approved_file_import",
        "ingestAllowed": True,
        "blockerId": None,
        "sourcePath": str(args.input),
        "sourceSha256": checksum,
        "counts": summarize(records),
        "warnings": [
            "Normalized candidates remain unverified discovery aids.",
            "Do not publish tax identifiers or personal applicant contacts.",
            "Grant award is not NYEOMSZSZ membership evidence.",
        ],
    }
    write_status(args.status_out, status)
    if args.normalized_out:
        args.normalized_out.parent.mkdir(parents=True, exist_ok=True)
        args.normalized_out.write_text(
            json.dumps({"schemaVersion": 1, "asOf": utc_now(), "records": records}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
