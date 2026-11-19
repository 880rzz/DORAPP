#!/usr/bin/env python3
"""Synchronize federation member event-source metadata from Ökoszisztéma.

The source catalog is authoritative for association calendar source settings.
Source links are not proof of event dates, accessibility, or ingestion success.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCE = "https://raw.githubusercontent.com/880rzz/okoszisztema/main/data/member-event-sources.json"
MIRROR = DATA / "member-event-sources-ecosystem.json"
ORGS = DATA / "organizations.json"
PUBLISHER = "880rzz/okoszisztema"


def valid_url(value):
    u = urlparse(str(value or ""))
    return u.scheme in {"https", "http"} and bool(u.netloc)


def validate(payload):
    if not isinstance(payload, dict) or payload.get("schemaVersion") != 1:
        raise ValueError("Unsupported federation source schema")
    if payload.get("sourceRepository") != PUBLISHER:
        raise ValueError("Unexpected federation authority")
    members = payload.get("members")
    if not isinstance(members, list) or len(members) != 29 or payload.get("organizationCount") != 29:
        raise ValueError("Expected exactly 29 federation members")
    if sum(len(m.get("calendarSources") or []) for m in members) != payload.get("sourceCount"):
        raise ValueError("Source count mismatch")
    ids, owners = set(), set()
    for member in members:
        mid, oid = member.get("memberId"), member.get("organizerId")
        if not mid or not oid or mid in ids or oid in owners:
            raise ValueError("Invalid or duplicate association member mapping")
        ids.add(mid)
        owners.add(oid)
        sources = member.get("calendarSources")
        if not isinstance(sources, list) or not sources:
            raise ValueError("Member missing program source: " + mid)
        urls, automatic = set(), set()
        for source in sources:
            if not isinstance(source, dict) or not source.get("label") or not source.get("kind"):
                raise ValueError("Invalid source metadata for " + mid)
            url = source.get("url")
            if not valid_url(url) or url in urls:
                raise ValueError("Invalid/duplicate source URL for " + mid)
            urls.add(url)
            if type(source.get("ingestEvents")) is not bool:
                raise ValueError("Missing explicit import authority for " + mid)
            if source["ingestEvents"]:
                if not str(url).startswith("https://") or source.get("scope") != "self":
                    raise ValueError("Unsafe automatic ingestion setting for " + mid)
                automatic.add(url)
        if not isinstance(member.get("eventSources"), list):
            raise ValueError("Missing legacy eventSources array for " + mid)
        if not set(member["eventSources"]).issubset(automatic):
            raise ValueError("Legacy sources must be approved automatic feeds for " + mid)
    return payload


def load(offline=False):
    if offline:
        return validate(json.loads(MIRROR.read_text(encoding="utf-8")))
    try:
        req = Request(SOURCE, headers={"User-Agent": "DORAPP-federation-sources/1.0", "Accept": "application/json"})
        with urlopen(req, timeout=12) as r:
            return validate(json.load(r))
    except Exception as exc:
        if not MIRROR.exists():
            raise
        print("WARN: Ökoszisztéma source temporarily unavailable; using validated mirror:", exc, file=sys.stderr)
        return validate(json.loads(MIRROR.read_text(encoding="utf-8")))


def synchronize(payload):
    organizations_doc = json.loads(ORGS.read_text(encoding="utf-8"))
    organizations = {o.get("id"): o for o in organizations_doc["organizations"]}
    # Validate the entire registry before writing anything.
    for m in payload["members"]:
        org = organizations.get(m["organizerId"])
        if not org or not any(x.get("umbrellaId") == "kozponti-szovetseg" for x in org.get("memberships", [])):
            raise ValueError("Association not an evidenced member: " + m["organizerId"])
    changed = 0
    for m in payload["members"]:
        org = organizations[m["organizerId"]]
        for field in ("calendarSources", "eventSources"):
            value = m[field]
            if org.get(field) != value:
                org[field] = value
                changed += 1
    mirror_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if not MIRROR.exists() or MIRROR.read_text(encoding="utf-8") != mirror_text:
        MIRROR.write_text(mirror_text, encoding="utf-8")
    if changed:
        organizations_doc["updated"] = datetime.now(timezone.utc).isoformat()
        ORGS.write_text(json.dumps(organizations_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Federation source authority: {len(payload['members'])} associations, "
          f"{payload['sourceCount']} sources, {changed} field changes")
    return changed


if __name__ == "__main__":
    synchronize(load("--offline" in sys.argv))
