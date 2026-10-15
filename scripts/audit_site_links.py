#!/usr/bin/env python3
"""Audit every rendered internal link and, optionally, every external HTTP link."""
import argparse
import json
import ssl
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://diaszpora.kozpontiszovetseg.at/"
HOST = urlparse(BASE).netloc
REPORT = ROOT / "data" / "link-audit.json"
UA = "DORAPP-Link-Audit/1.0 (+https://diaszpora.kozpontiszovetseg.at/)"


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        if tag == "a" and "href" in values:
            self.links.append(values["href"].strip())


def parse_page(path):
    parser = LinkParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return parser


def target_path(parsed):
    raw = unquote(parsed.path or "/").lstrip("/")
    if not raw:
        return ROOT / "index.html"
    candidate = ROOT / raw
    if parsed.path.endswith("/") or candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate


def audit_internal(pages):
    parsed_pages = {path: parse_page(path) for path in pages}
    errors = []
    external = set()
    checked = 0
    for page, document in parsed_pages.items():
        page_url = urljoin(BASE, page.relative_to(ROOT).as_posix())
        for href in document.links:
            if not href:
                errors.append({"page": str(page.relative_to(ROOT)), "href": href, "error": "empty-link"})
                continue
            if href.startswith(("mailto:", "tel:")):
                if href.endswith(":"):
                    errors.append({"page": str(page.relative_to(ROOT)), "href": href, "error": "empty-contact-link"})
                continue
            if href.startswith(("javascript:", "data:")):
                errors.append({"page": str(page.relative_to(ROOT)), "href": href, "error": "unsafe-link-scheme"})
                continue
            absolute = urljoin(page_url, href)
            parsed = urlparse(absolute)
            if parsed.scheme not in {"http", "https"}:
                continue
            if parsed.netloc != HOST:
                external.add(absolute.split("#", 1)[0])
                continue
            checked += 1
            target = target_path(parsed)
            if not target.exists():
                errors.append({"page": str(page.relative_to(ROOT)), "href": href, "error": "missing-target"})
                continue
            if parsed.fragment and target.suffix.lower() in {".html", ".htm"}:
                target_doc = parsed_pages.get(target)
                if target_doc is None:
                    target_doc = parse_page(target)
                    parsed_pages[target] = target_doc
                if parsed.fragment not in target_doc.ids:
                    errors.append({"page": str(page.relative_to(ROOT)), "href": href, "error": "missing-anchor"})
    return checked, sorted(external), errors


def check_external(url):
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/json,application/pdf,*/*;q=0.5"})
    try:
        with urllib.request.urlopen(request, timeout=12, context=ssl.create_default_context()) as response:
            response.read(2048)
            code = getattr(response, "status", 200)
            return {"url": url, "status": "ok" if code < 400 else "http-error", "httpStatus": code, "resolvedUrl": response.geturl()}
    except urllib.error.HTTPError as exc:
        status = "rate-limited" if exc.code == 429 else "site-blocked" if exc.code in {401, 403} else "not-found" if exc.code in {404, 410} else "http-error"
        return {"url": url, "status": status, "httpStatus": exc.code, "resolvedUrl": exc.geturl() or url}
    except ssl.SSLError:
        return {"url": url, "status": "tls-error", "httpStatus": None, "resolvedUrl": url}
    except urllib.error.URLError as exc:
        reason = str(getattr(exc, "reason", "")).lower()
        status = "timeout" if "timed out" in reason else "tls-error" if "ssl" in reason or "certificate" in reason else "network-error"
        return {"url": url, "status": status, "httpStatus": None, "resolvedUrl": url}
    except TimeoutError:
        return {"url": url, "status": "timeout", "httpStatus": None, "resolvedUrl": url}
    except Exception:
        return {"url": url, "status": "network-error", "httpStatus": None, "resolvedUrl": url}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-external", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    pages = sorted(path for path in ROOT.rglob("*.html") if ".git" not in path.parts)
    internal_count, external_urls, internal_errors = audit_internal(pages)
    external_results = []
    if args.check_external:
        with ThreadPoolExecutor(max_workers=16) as pool:
            futures = {pool.submit(check_external, url): url for url in external_urls}
            for future in as_completed(futures):
                external_results.append(future.result())
        external_results.sort(key=lambda item: item["url"])
    status_counts = {}
    for item in external_results:
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1
    report = {
        "updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "pages": len(pages),
        "internalLinksChecked": internal_count,
        "internalErrors": internal_errors,
        "externalLinksDiscovered": len(external_urls),
        "externalLinksChecked": len(external_results),
        "externalStatusCounts": status_counts,
        "externalResults": external_results,
        "policy": "Only broken internal links fail validation. External technical failures require review and never prove entity inactivity."
    }
    if not args.no_write:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"link_audit pages={len(pages)} internal={internal_count} internal_errors={len(internal_errors)} external={len(external_results)}")
    if internal_errors:
        for item in internal_errors[:100]:
            print("ERROR:", json.dumps(item, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
