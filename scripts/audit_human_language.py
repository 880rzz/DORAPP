#!/usr/bin/env python3
"""Reject internal implementation jargon from visitor-facing HTML."""
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data" / "human-language-audit.json"
BANNED = {
    "legacy-jargon": re.compile(r"\blegacy[- ](?:only|profile|source|surface)\b|legacy\s*/", re.I),
    "parity-jargon": re.compile(r"\b(?:Austria|country)[- ]parity\b|parity country component", re.I),
    "ingestion": re.compile(r"\bingest(?:ion)?\b", re.I),
    "host-institution": re.compile(r"host-institution", re.I),
    "activity-record": re.compile(r"activity\s+rekord", re.I),
    "steward-jargon": re.compile(r"steward[\s‑-]*(?:ellenőrzés|audit)", re.I),
    "automatic-legacy": re.compile(r"automatikus\s*/\s*legacy", re.I),
}


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "template"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "template"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(data.strip())


def main():
    findings = []
    pages = sorted(ROOT.rglob("*.html"))
    for path in pages:
        if ".git" in path.parts:
            continue
        parser = VisibleText()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        text = " ".join(parser.parts)
        for rule, pattern in BANNED.items():
            match = pattern.search(text)
            if match:
                findings.append({"page": str(path.relative_to(ROOT)), "rule": rule, "excerpt": text[max(0, match.start()-55):match.end()+55]})
    report = {
        "updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "pagesChecked": len(pages),
        "findings": findings,
        "gmailStyleProfileApplied": False,
        "gmailStyleProfileNote": "No authorized Gmail connector was available; no personal writing style was inferred."
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"human_language pages={len(pages)} findings={len(findings)}")
    if findings:
        for item in findings[:100]:
            print("ERROR:", json.dumps(item, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
