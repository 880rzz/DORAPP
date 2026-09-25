#!/usr/bin/env python3
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]
BASE="https://diaszpora.kozpontiszovetseg.at"
org=json.loads((ROOT/"data/organizations.json").read_text(encoding="utf-8"))
edu=json.loads((ROOT/"data/education.json").read_text(encoding="utf-8"))

urls=[
    f"{BASE}/",
    f"{BASE}/forrasok.html",
    f"{BASE}/llms.txt",
    f"{BASE}/ai.txt",
]
urls += [f"{BASE}/szervezetek/{x['id']}.html" for x in org.get("organizations",[])]
urls += [f"{BASE}/oktatas/{x['id']}.html" for x in edu.get("institutions",[])]

xml=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in urls:
    xml.append(f"  <url><loc>{escape(u)}</loc></url>")
xml.append("</urlset>")
(ROOT/"sitemap.xml").write_text("\n".join(xml)+"\n",encoding="utf-8")
print(f"sitemap_urls={len(urls)}")
