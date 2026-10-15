#!/usr/bin/env python3
"""Audit publishable country datasets for profiles, evidence and public reachability."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
READY = {"reviewed", "verified-zero"}
REPORT = DATA / "ecosystem-quality-audit.json"


def read(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def rows(document, keys):
    for key in keys:
        if isinstance(document.get(key), list):
            return document[key]
    return []


def urls(entity):
    result = []
    for key in ("website", "facebook", "instagram", "youtube", "linkedin", "contactUrl"):
        if entity.get(key):
            result.append(entity[key])
    for key in ("publicChannels", "evidenceSources", "calendarSources", "eventSources"):
        for item in entity.get(key) or []:
            if isinstance(item, str):
                result.append(item)
            elif item.get("url"):
                result.append(item["url"])
    return list(dict.fromkeys(result))


def has_social(entity):
    if any(entity.get(key) for key in ("facebook", "instagram", "youtube", "linkedin")):
        return True
    social = {"facebook", "instagram", "youtube", "linkedin", "tiktok", "x"}
    return any(str(item.get("platform", "")).lower() in social for item in entity.get("publicChannels") or [] if isinstance(item, dict))


def main():
    registry = read(DATA / "global.json", {"countries": []})
    countries = []
    blocking = []
    totals = {"organizations": 0, "education": 0, "missingContact": 0, "missingSocial": 0, "missingEventSource": 0}
    for country in registry.get("countries", []):
        if country.get("researchStatus") not in READY:
            continue
        iso = country.get("iso2")
        base = DATA / "countries" / iso
        orgs = [x for x in rows(read(base / "organizations.json", {}), ("organizations", "items")) if x.get("entityClass") != "activity"]
        education = rows(read(base / "education.json", {}), ("institutions", "education", "items"))
        issues = []
        missing_contact = []
        missing_social = []
        missing_event_source = []
        for entity in orgs:
            eid = entity.get("id")
            if not eid or not entity.get("name"):
                issues.append({"id": eid, "error": "missing-id-or-name"})
                continue
            if not (entity.get("intro") or entity.get("summary")):
                issues.append({"id": eid, "error": "missing-description"})
            if not entity.get("evidenceSources"):
                issues.append({"id": eid, "error": "missing-evidence"})
            if not urls(entity):
                issues.append({"id": eid, "error": "missing-public-url"})
            if not (ROOT / "countries" / iso / "organizations" / f"{eid}.html").exists():
                issues.append({"id": eid, "error": "missing-profile"})
            if not any(entity.get(key) for key in ("email", "phone", "contactUrl")):
                missing_contact.append(eid)
            if not has_social(entity):
                missing_social.append(eid)
            if not (entity.get("calendarSources") or entity.get("eventSources")):
                missing_event_source.append(eid)
        for entity in education:
            eid = entity.get("id")
            if not eid or not entity.get("name"):
                issues.append({"id": eid, "error": "education-missing-id-or-name"})
                continue
            if not (entity.get("intro") or entity.get("summary")):
                issues.append({"id": eid, "error": "education-missing-description"})
            if not (entity.get("evidenceSources") or entity.get("sourceUrl")):
                issues.append({"id": eid, "error": "education-missing-evidence"})
            if not (ROOT / "countries" / iso / "education" / f"{eid}.html").exists():
                issues.append({"id": eid, "error": "education-missing-profile"})
        completion = read(base / "research-completion.json", {})
        completion_state = completion.get("completionStatus") or ("austria-canonical" if iso == "at" else "missing")
        country_result = {
            "country": iso,
            "researchStatus": country.get("researchStatus"),
            "completionStatus": completion_state,
            "organizations": len(orgs),
            "education": len(education),
            "blockingIssues": issues,
            "missingPublicContact": missing_contact,
            "missingVerifiedSocialChannel": missing_social,
            "missingEventSource": missing_event_source,
        }
        countries.append(country_result)
        totals["organizations"] += len(orgs)
        totals["education"] += len(education)
        totals["missingContact"] += len(missing_contact)
        totals["missingSocial"] += len(missing_social)
        totals["missingEventSource"] += len(missing_event_source)
        blocking.extend({"country": iso, **item} for item in issues)
    report = {
        "updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "readyCountries": len(countries),
        "totals": totals,
        "countries": countries,
        "blockingIssues": blocking,
        "policy": "Missing public contact, social or event sources are review queues, not permission to invent data or archive an entity."
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ecosystem_quality ready={len(countries)} organizations={totals['organizations']} education={totals['education']} blocking={len(blocking)}")
    if blocking:
        for item in blocking[:100]:
            print("ERROR:", json.dumps(item, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
