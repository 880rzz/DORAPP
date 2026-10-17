#!/usr/bin/env python3
"""Decide daily refresh from committed evidence and report schedule gaps."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def utc_date(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).date()
    except (AttributeError, TypeError, ValueError):
        return None


def decide(now, press, state):
    today = now.date()
    daily_due = utc_date(press.get("lastRunAt")) != today
    previous = state.get("lastRunAt")
    gap_hours = None
    if previous:
        try:
            gap_hours = (now - datetime.fromisoformat(previous.replace("Z", "+00:00")).astimezone(timezone.utc)).total_seconds() / 3600
        except ValueError:
            pass
    return daily_due, gap_hours


def main():
    def read(path):
        try:
            return json.loads((ROOT / path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    now = datetime.now(timezone.utc)
    due, gap = decide(now, read("data/global-press-review-queue.json"), read("data/research-state.json"))
    output = Path(os.environ["GITHUB_OUTPUT"])
    with output.open("a", encoding="utf-8") as file:
        file.write(f"daily_due={str(due).lower()}\n")
    print(f"Daily event and press refresh due: {due}")
    if gap is not None:
        print(f"Time since last committed research: {gap:.2f} hours")
        if gap > 2:
            print(f"::warning::Hourly research is late: {gap:.2f} hours since last committed run")


if __name__ == "__main__":
    main()
