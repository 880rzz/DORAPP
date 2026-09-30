#!/usr/bin/env python3
import json, urllib.parse, urllib.request, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GLOBAL = DATA / "global.json"
STATE = DATA / "research-state.json"
RUNS = DATA / "daily-runs"
BATCH_SIZE = 8
TIMEOUT = 20
UA = "DORAPP-Global-Steward/1.0 (+https://diaszpora.kozpontiszovetseg.at/)"

QUERY_TEMPLATES = [
    ("hu", "magyar egyesület {country}"),
    ("hu", "magyar közösség {country}"),
    ("hu", "magyar iskola {country}"),
    ("hu", "magyar cserkész {country}"),
    ("en", "Hungarian association {country}"),
    ("en", "Hungarian community {country}"),
    ("en", "Hungarian school {country}"),
    ("en", "Hungarian church {country}"),
]

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))

def country_name(c):
    n = c.get("name") or {}
    for key in ("hu", "en", "de"):
        if n.get(key) and len(n[key]) > 2:
            return n[key]
    return c["iso2"].upper()

def wikipedia_search(lang, query):
    endpoint = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "format": "json",
        "utf8": "1",
        "srlimit": "8",
        "srsearch": query,
    }
    url = endpoint + "?" + urllib.parse.urlencode(params)
    data = fetch_json(url)
    out = []
    for row in data.get("query", {}).get("search", []):
        title = row.get("title")
        if not title:
            continue
        out.append({
            "title": title,
            "url": f"https://{lang}.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")),
            "sourceType": "wikipedia-discovery",
            "language": lang,
            "query": query,
        })
    return out

def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {
        "schemaVersion": 1,
        "cursor": 0,
        "batchSize": BATCH_SIZE,
        "lastRunAt": None,
        "countriesAttempted": [],
    }

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def select_batch(countries, state):
    eligible = [c for c in countries if c.get("iso2") != "at"]
    ranked = sorted(
        eligible,
        key=lambda c: (
            {"unresearched": 0, "researching": 1, "partial": 2, "reviewed": 3, "verified-zero": 4}.get(c.get("researchStatus"), 9),
            c.get("lastBroadVerifiedAt") or "",
            c["iso2"],
        ),
    )
    if not ranked:
        return []
    cursor = int(state.get("cursor", 0)) % len(ranked)
    batch = []
    i = cursor
    while len(batch) < min(BATCH_SIZE, len(ranked)):
        batch.append(ranked[i])
        i = (i + 1) % len(ranked)
    state["cursor"] = i
    return batch

def merge_candidates(existing, new_items, checked_at):
    by_url = {x.get("url"): x for x in existing if x.get("url")}
    for item in new_items:
        url = item["url"]
        if url not in by_url:
            item["discoveredAt"] = checked_at
            item["status"] = "candidate"
            by_url[url] = item
        else:
            by_url[url]["lastSeenAt"] = checked_at
    return sorted(by_url.values(), key=lambda x: (x.get("sourceType",""), x.get("title",""), x.get("url","")))

def main():
    g = json.loads(GLOBAL.read_text(encoding="utf-8"))
    state = load_state()
    checked_at = now_iso()
    batch = select_batch(g.get("countries", []), state)

    attempted, completed, failed = [], [], []
    total_candidates = 0

    for c in batch:
        iso = c["iso2"]
        name = country_name(c)
        attempted.append(iso)
        country_dir = DATA / "countries" / iso
        discovery_path = country_dir / "discovery-sources.json"
        existing_doc = {"updated": None, "country": iso, "sources": []}
        if discovery_path.exists():
            try:
                existing_doc = json.loads(discovery_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        found = []
        errors = []
        for lang, template in QUERY_TEMPLATES:
            q = template.format(country=name)
            try:
                found.extend(wikipedia_search(lang, q))
            except Exception as e:
                errors.append({"query": q, "error": type(e).__name__})
            time.sleep(0.15)

        sources = merge_candidates(existing_doc.get("sources", []), found, checked_at)
        total_candidates += len(sources)
        save_json(discovery_path, {
            "updated": checked_at,
            "country": iso,
            "researchRole": "secondary discovery only; candidates require first-party verification before publication",
            "sources": sources,
            "errors": errors,
        })

        c["researchStatus"] = "researching"
        c["lastResearchAttemptAt"] = checked_at
        c["discoveryCandidateCount"] = len(sources)
        if errors and not sources:
            failed.append(iso)
        else:
            completed.append(iso)

    state["lastRunAt"] = checked_at
    state["batchSize"] = BATCH_SIZE
    state["countriesAttempted"] = attempted
    state["countriesCompleted"] = completed
    state["countriesFailed"] = failed
    save_json(STATE, state)
    save_json(GLOBAL, g)

    RUNS.mkdir(parents=True, exist_ok=True)
    stamp = checked_at[:10]
    save_json(RUNS / f"{stamp}-global-research.json", {
        "timestamp": checked_at,
        "countriesAttempted": attempted,
        "countriesCompleted": completed,
        "countriesFailed": failed,
        "discoveryCandidatesAcrossBatch": total_candidates,
        "mode": "candidate-discovery",
        "publicationPolicy": "No candidate is promoted to a canonical organization without first-party verification.",
    })
    print(json.dumps({
        "attempted": attempted,
        "completed": completed,
        "failed": failed,
        "candidateCount": total_candidates
    }))

if __name__ == "__main__":
    main()
