#!/usr/bin/env python3
"""Decide daily refresh from committed evidence and report schedule gaps.

A successful steward run is not organization verification, country completion,
or proof that production was updated. This helper only answers:
- is the independent daily event/press refresh due?
- how long since the last committed research-state timestamp?
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOURLY_LATE_HOURS = 2.0


def utc_date(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).date()
    except (AttributeError, TypeError, ValueError):
        return None


def decide(now, press, state, late_after_hours=HOURLY_LATE_HOURS):
    today = now.date()
    daily_due = utc_date(press.get("lastRunAt")) != today
    previous = state.get("lastRunAt")
    gap_hours = None
    if previous:
        try:
            gap_hours = (
                now - datetime.fromisoformat(previous.replace("Z", "+00:00")).astimezone(timezone.utc)
            ).total_seconds() / 3600
        except ValueError:
            gap_hours = None
    late = gap_hours is not None and gap_hours > late_after_hours
    return {
        "daily_due": daily_due,
        "gap_hours": gap_hours,
        "hourly_late": late,
        "last_research_at": previous,
        "press_last_run_at": press.get("lastRunAt"),
    }


def read_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--press", default="data/global-press-review-queue.json")
    parser.add_argument("--state", default="data/research-state.json")
    parser.add_argument("--write-github-output", action="store_true", default=True)
    parser.add_argument("--no-write-github-output", action="store_false", dest="write_github_output")
    args = parser.parse_args(argv)

    now = datetime.now(timezone.utc)
    decision = decide(now, read_json(ROOT / args.press), read_json(ROOT / args.state))

    if args.write_github_output:
        github_output = os.environ.get("GITHUB_OUTPUT")
        if not github_output:
            print("GITHUB_OUTPUT is not set; passing --no-write-github-output for local use", file=sys.stderr)
            return 2
        with Path(github_output).open("a", encoding="utf-8") as handle:
            handle.write(f"daily_due={str(decision['daily_due']).lower()}\n")
            handle.write(f"hourly_late={str(decision['hourly_late']).lower()}\n")
            if decision["gap_hours"] is not None:
                handle.write(f"gap_hours={decision['gap_hours']:.4f}\n")

    print(f"Daily event and press refresh due: {decision['daily_due']}")
    if decision["gap_hours"] is not None:
        print(f"Time since last committed research: {decision['gap_hours']:.2f} hours")
        if decision["hourly_late"]:
            print(
                f"::warning::Hourly research appears late: {decision['gap_hours']:.2f} hours since last committed run"
            )
    else:
        print("No committed research-state timestamp available for gap detection")
    print(
        "Reminder: schedule success != verified organization promotion, country completion, or live production update."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
