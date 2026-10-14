#!/usr/bin/env python3
"""Refresh event feeds for every non-Austrian country with canonical entities.

Austria keeps its established compatibility pipeline in update_events.py. This
runner uses the same parsers, but writes country-scoped events and health so a
failure in one country or source cannot erase another country's results.
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import update_events as core


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ACTIVE_STATUSES = {"researching", "partial", "reviewed"}


def read_json(path: Path, fallback: dict) -> dict:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def entity_adapter(entity: dict) -> dict:
    """Provide the legacy parser keys without changing canonical entities."""
    return {
        **entity,
        "state": entity.get("region") or entity.get("state"),
        "city": entity.get("city"),
    }


def ingest_sources(entity: dict):
    for source in entity.get("calendarSources") or []:
        if not isinstance(source, dict) or source.get("ingestEvents") is not True:
            continue
        url = str(source.get("url") or "").strip()
        if url:
            yield {**source, "url": url}


def country_event(event: dict, country: str) -> dict:
    result = dict(event)
    result["country"] = country
    result["region"] = result.pop("state", None)
    result["organizerId"] = result.pop("organizationId", None)
    result["sourceType"] = result.get("sourceType") or "automatic-structured-source"
    return {key: value for key, value in result.items() if value not in (None, "", [], {})}


def internal_event(event: dict) -> dict:
    result = dict(event)
    result["organizationId"] = result.get("organizationId") or result.get("organizerId")
    result["state"] = result.get("state") or result.get("region")
    return result


def audit_source(entity: dict, source_cfg: dict):
    source = source_cfg["url"]
    row = {
        "entityId": entity["id"],
        "entityType": entity["_entityType"],
        "source": source,
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "status": "unknown",
        "eventsFound": 0,
        "pagesChecked": 0,
    }
    if source_cfg.get("inclusionRule") and not source_cfg.get("includeRegex"):
        row["status"] = "configuration-error"
        row["error"] = "inclusionRule requires includeRegex before automatic ingestion"
        return row, []

    collected = []
    try:
        events, candidates, content_type = core.collect_page(source, entity, source)
        row["pagesChecked"] = 1
        if content_type == "application/pdf" or source.lower().endswith(".pdf"):
            row["status"] = "parser-gap"
            row["error"] = "PDF event source requires a dedicated parser"
            return row, []
        collected.extend(e for e in events if core.futureish(e["startDate"], e.get("endDate")))
        for url in candidates:
            try:
                subevents, _, sub_type = core.collect_page(url, entity, source)
                row["pagesChecked"] += 1
                if sub_type != "application/pdf" and not url.lower().endswith(".pdf"):
                    collected.extend(
                        e for e in subevents if core.futureish(e["startDate"], e.get("endDate"))
                    )
            except Exception:
                continue
        collected = core.dedupe_events(collected)
        collected = [e for e in collected if core.source_event_allowed(e, source_cfg)]
        row["eventsFound"] = len(collected)
        row["status"] = "ok-events" if collected else "ok-no-structured-event"
    except Exception as ex:
        code = getattr(ex, "code", None)
        message = str(ex)
        if code in (401, 403):
            row["status"] = "site-blocked"
        elif code == 429:
            row["status"] = "rate-limited"
        elif "CERTIFICATE_VERIFY_FAILED" in message or "SSL:" in message:
            row["status"] = "tls-error"
        elif any(
            token in message
            for token in (
                "Network is unreachable",
                "No address associated with hostname",
                "Name or service not known",
                "Connection refused",
                "timed out",
            )
        ):
            row["status"] = "network-error"
        else:
            row["status"] = "error"
        row["error"] = message[:220]
    return row, collected


def refresh_country(country: str) -> tuple[int, int]:
    country_dir = DATA / "countries" / country
    organizations = read_json(country_dir / "organizations.json", {"organizations": []}).get(
        "organizations", []
    )
    education_doc = read_json(country_dir / "education.json", {"institutions": []})
    institutions = education_doc.get(
        "institutions", education_doc.get("education", education_doc.get("items", []))
    )
    entities = []
    for entity_type, items in (("organization", organizations), ("education", institutions)):
        for item in items:
            entity = entity_adapter(item)
            entity["_entityType"] = entity_type
            entities.append(entity)

    jobs = [
        (entity, source_cfg)
        for entity in entities
        for source_cfg in ingest_sources(entity)
    ]
    events_path = country_dir / "events.json"
    old_doc = read_json(events_path, {"events": []})
    merged = {}
    for event in old_doc.get("events", old_doc.get("items", [])):
        internal = internal_event(event)
        if core.futureish(internal.get("startDate"), internal.get("endDate")):
            merged[internal["id"]] = internal

    health = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(audit_source, entity, source_cfg) for entity, source_cfg in jobs]
        for future in as_completed(futures):
            row, collected = future.result()
            health.append(row)
            for event in collected:
                merged[event["id"]] = event

    health.sort(key=lambda row: (row["entityType"], row["entityId"], row["source"]))
    events = sorted(core.dedupe_events(merged.values()), key=lambda event: str(event.get("startDate", "")))
    for event in events:
        event["programCategories"] = list(
            dict.fromkeys(list(event.get("programCategories") or []) + core.classify_program_categories(event))
        )
    now = datetime.now(timezone.utc).isoformat()
    events_path.write_text(
        json.dumps(
            {
                "updated": now,
                "verificationStatus": "automated-source-refresh-with-manual-provenance",
                "programCategoryDefinitions": core.PROGRAM_CATEGORY_DEFINITIONS,
                "events": [country_event(event, country) for event in events],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (country_dir / "event-source-health.json").write_text(
        json.dumps({"updated": now, "country": country, "sources": health}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(f"country={country} entities={len(entities)} sources={len(health)} events={len(events)}")
    return len(health), len(events)


def main(argv: list[str]) -> int:
    registry = read_json(DATA / "global.json", {"countries": []})
    requested = {value.lower() for value in argv[1:]}
    countries = []
    for row in registry.get("countries", []):
        country = str(row.get("iso2") or "").lower()
        if country == "at" or row.get("researchStatus") not in ACTIVE_STATUSES:
            continue
        if requested and country not in requested:
            continue
        countries.append(country)
    for country in countries:
        refresh_country(country)
    print(f"countries={len(countries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
