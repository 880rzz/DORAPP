#!/usr/bin/env python3
"""Annotate verification-queue items with recommended lifecycle states.

Does not publish organizations. Secondary/wikipedia-only items remain blocked
from PUBLISHABLE/PUBLISHED recommendations.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import evidence_lifecycle

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "data" / "verification-queue.json"


def recommend(item: dict) -> str:
    status = (item.get("firstPartyStatus") or "").lower()
    sources = []
    if item.get("secondaryUrl"):
        host = item["secondaryUrl"]
        source_type = "wikipedia" if "wikipedia.org" in host else "secondary"
        sources.append({"sourceType": source_type, "url": host})
    for url in item.get("firstPartyCandidates") or []:
        sources.append({"sourceType": "candidate", "url": url})

    if status in {"verified-promotion-ready"}:
        return "FIRST_PARTY_CHECKED"
    if status in {"verified-partial"}:
        return "NEEDS_REVIEW"
    if status in {"verification-error"}:
        return "NEEDS_REVIEW"
    if evidence_lifecycle.secondary_mention_alone_blocks_verification(
        [{"sourceType": "wikipedia" if "wikipedia.org" in (item.get("secondaryUrl") or "") else "secondary"}]
    ) and not item.get("firstPartyCandidates"):
        return "REJECTED"
    # Wikipedia + weak candidates still not publishable.
    if "wikipedia.org" in (item.get("secondaryUrl") or "") and status == "no-strong-first-party-proof":
        return "REJECTED"
    return "DISCOVERED"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Persist recommendedLifecycle onto queue items")
    args = parser.parse_args()
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for item in queue.get("items") or []:
        recommendation = recommend(item)
        counts[recommendation] = counts.get(recommendation, 0) + 1
        if args.write:
            item["recommendedLifecycle"] = recommendation
            item["publishBlockedReason"] = None
            if recommendation in {"REJECTED", "DISCOVERED", "NEEDS_REVIEW"}:
                item["publishBlockedReason"] = "insufficient-first-party-evidence"
    if args.write:
        QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"annotated": sum(counts.values()), "recommendations": counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
