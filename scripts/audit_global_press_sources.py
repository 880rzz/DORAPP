#!/usr/bin/env python3
"""Non-mutating global press coverage audit. Never promotes unverified mentions."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES = ROOT / "data" / "countries"

def main():
    count = 0
    with_press = 0
    missing = []
    malformed = []
    for path in sorted(COUNTRIES.glob("*/organizations.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for org in data.get("organizations", []):
            count += 1
            mentions = org.get("pressMentions", org.get("press", []))
            if not isinstance(mentions, list):
                malformed.append(f"{path.parent.name}:{org.get('id','?')}")
                continue
            if not mentions:
                missing.append(f"{path.parent.name}:{org.get('id','?')}")
            else:
                with_press += 1
            for item in mentions:
                if not isinstance(item, dict) or not str(item.get("url","")).startswith(("https://","http://")):
                    malformed.append(f"{path.parent.name}:{org.get('id','?')}:invalid-press-url")
    print(json.dumps({"checkedAt": datetime.now(timezone.utc).isoformat(), "organizations":count, "withPress":with_press, "withoutPress":len(missing), "missingExamples":missing[:25], "malformed":malformed[:25]}, ensure_ascii=False, indent=2))
    if malformed:
        raise SystemExit("Malformed press entries detected")

if __name__ == "__main__":
    main()
