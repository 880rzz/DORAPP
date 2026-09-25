#!/usr/bin/env python3
import json, subprocess, urllib.request
from urllib.parse import quote
from pathlib import Path

BASE="https://diaszpora.kozpontiszovetseg.at"
HOST="diaszpora.kozpontiszovetseg.at"
KEY="9f12a6c4d78b4e2fa3c1b6590d7e8a42"
ROOT=Path(__file__).resolve().parents[1]

def changed_files():
    try:
        out=subprocess.check_output(["git","diff","--name-only","HEAD^","HEAD"],cwd=ROOT,text=True)
        return [x.strip() for x in out.splitlines() if x.strip()]
    except Exception:
        return []

def to_url(path):
    if path=="index.html": return BASE+"/"
    if path in ("forrasok.html","adatminoseg.html","llms.txt","ai.txt","ai-entry.json","entity.jsonld","sitemap.xml"): return BASE+"/"+path
    for prefix in ("szervezetek/","oktatas/","esemenyek/","tartomanyok/","kategoriak/"):
        if path.startswith(prefix) and path.endswith(".html"):
            return BASE+"/"+quote(path,safe="/")
    if path.startswith("data/") and path.endswith(".json"):
        return BASE+"/"+path
    return None

files=changed_files()
urls=[]
for p in files:
    u=to_url(p)
    if u and u not in urls: urls.append(u)
if any(p.startswith(("data/","scripts/")) for p in files):
    if BASE+"/" not in urls: urls.append(BASE+"/")
if not urls:
    print("indexnow: no changed public URLs")
    raise SystemExit(0)

payload=json.dumps({
    "host":HOST,
    "key":KEY,
    "keyLocation":f"{BASE}/{KEY}.txt",
    "urlList":urls[:10000]
}).encode("utf-8")
req=urllib.request.Request("https://api.indexnow.org/indexnow",data=payload,headers={"Content-Type":"application/json; charset=utf-8","User-Agent":"DORAPP-IndexNow/1.0"},method="POST")
try:
    with urllib.request.urlopen(req,timeout=20) as r:
        print("indexnow:",r.status,"urls=",len(urls))
except Exception as ex:
    print("indexnow warning:",ex,"urls=",len(urls))
