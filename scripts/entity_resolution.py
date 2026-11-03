#!/usr/bin/env python3
"""Deterministic entity resolution helpers that preserve stable IDs."""

from __future__ import annotations

import re
import unicodedata
import urllib.parse
from typing import Any


def slug(value: str, limit: int = 90) -> str:
    normalized = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii").lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized[:limit] or "entity"


def host_of(url: str | None) -> str | None:
    if not url:
        return None
    host = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    return host or None


def normalize_name(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().casefold()


def allocate_stable_id(base_name: str, used_ids: set[str]) -> str:
    base = slug(base_name)
    candidate = base
    index = 2
    while candidate in used_ids:
        candidate = f"{base}-{index}"
        index += 1
    return candidate


def find_duplicate(
    candidate: dict[str, Any],
    existing: list[dict[str, Any]],
    *,
    require_same_country: bool = True,
) -> dict[str, Any] | None:
    """Match by official website host+path or exact name+city within country.

    Cross-border IE/GB collisions are blocked when countries differ.
    """
    cand_country = (candidate.get("country") or candidate.get("iso2") or "").lower()
    cand_host = host_of(candidate.get("website") or candidate.get("officialWebsite"))
    cand_website = (candidate.get("website") or candidate.get("officialWebsite") or "").rstrip("/")
    cand_name = normalize_name(candidate.get("name") or candidate.get("displayName") or candidate.get("legalName"))
    cand_city = normalize_name(candidate.get("city"))

    for row in existing:
        row_country = (row.get("country") or row.get("iso2") or "").lower()
        if require_same_country and cand_country and row_country and cand_country != row_country:
            continue
        row_host = host_of(row.get("website") or row.get("officialWebsite"))
        row_website = (row.get("website") or row.get("officialWebsite") or "").rstrip("/")
        if cand_host and row_host and cand_host == row_host and cand_website == row_website:
            return row
        row_name = normalize_name(row.get("name") or row.get("displayName") or row.get("legalName"))
        row_city = normalize_name(row.get("city"))
        if cand_name and row_name and cand_name == row_name and cand_city and cand_city == row_city:
            return row
    return None


def merge_aliases(existing: dict[str, Any], incoming: dict[str, Any]) -> list[str]:
    values = []
    for source in (existing, incoming):
        for key in ("aliases", "alternateNames"):
            raw = source.get(key) or []
            if isinstance(raw, str):
                values.append(raw)
            else:
                values.extend(str(x) for x in raw)
        for key in ("name", "displayName", "legalName"):
            if source.get(key):
                values.append(str(source[key]))
    seen = set()
    out = []
    for value in values:
        key = normalize_name(value)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out
