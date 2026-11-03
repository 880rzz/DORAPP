#!/usr/bin/env python3
"""Classify production JSON dataset responses for smoke diagnostics.

Distinguishes missing optional datasets, HTML/error bodies, empty payloads,
and schema mismatches. A transient CDN body must not be silently labeled as
git-side JSON syntax corruption without evidence.
"""

from __future__ import annotations

import argparse
import json
from typing import Any


def classify_dataset_response(
    *,
    iso: str,
    route: str,
    status: str,
    body: str,
    required_keys: tuple[str, ...],
    optional: bool,
) -> tuple[str, str | None]:
    """Return (category, failure_message_or_none).

    Categories: ok, absent_optional, http_error, empty_body, html_body,
    invalid_json, unexpected_shape.
    """
    if status == "404" and optional:
        return "absent_optional", None
    if status != "200":
        return "http_error", f"{iso}: HTTP {status} {route}"
    if not body.strip():
        return "empty_body", f"{iso}: empty body {route}"
    lowered = body.lstrip().lower()
    if lowered.startswith("<!doctype html") or lowered.startswith("<html"):
        return "html_body", f"{iso}: HTML body instead of JSON {route}"
    try:
        payload = json.loads(body)
    except ValueError as exc:
        preview = body[:80].replace("\n", "\\n")
        return "invalid_json", f"{iso}: invalid JSON {route} ({exc}); body_prefix={preview!r}"
    if not isinstance(payload, dict) or not any(key in payload for key in required_keys):
        return "unexpected_shape", f"{iso}: unexpected dataset shape {route}"
    return "ok", None


def summarize(failures: list[str], absent: list[str], categories: dict[str, int]) -> str:
    lines = [
        f"Country dataset probe categories: {json.dumps(categories, sort_keys=True)}",
        f"unpublished optional datasets: {len(absent)}",
    ]
    if absent:
        lines.append("DATA COVERAGE GAPS (not verified empty):")
        lines.extend(absent[:80])
    if failures:
        lines.append("Production country parity failed:")
        lines.extend(failures[:40])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Run built-in classification demos")
    args = parser.parse_args()
    if args.demo:
        demos: list[tuple[Any, ...]] = [
            ("es", "/data/countries/es/organizations.json", "200", '{"organizations":[]}', ("organizations",), True),
            ("es", "/data/countries/es/organizations.json", "200", "<!DOCTYPE html><html>", ("organizations",), True),
            ("xx", "/data/countries/xx/organizations.json", "404", "missing", ("organizations",), True),
            ("es", "/data/countries/es/organizations.json", "200", "{not-json", ("organizations",), True),
        ]
        for demo in demos:
            print(classify_dataset_response(
                iso=demo[0],
                route=demo[1],
                status=demo[2],
                body=demo[3],
                required_keys=demo[4],
                optional=demo[5],
            ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
