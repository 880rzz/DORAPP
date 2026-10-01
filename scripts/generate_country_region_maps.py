#!/usr/bin/env python3
"""Generate repository-owned first-level administrative SVG maps from Natural Earth."""
import json, math, re, shutil, tempfile, urllib.request, zipfile
from collections import defaultdict
from pathlib import Path
import shapefile
import pycountry

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"assets"/"maps"
OUT.mkdir(parents=True,exist_ok=True)
VERSION="5.1.1"
SOURCE="https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_1_states_provinces.zip"
MANIFEST=OUT/"source.json"

def esc(v):
    return str(v or "").replace("&","&amp;").replace('"',"&quot;").replace("<","&lt;").replace(">","&gt;")

def slug(v):
    return re.sub(r"[^a-z0-9]+","-",str(v).lower()).strip("-")

COUNTRY_NAME_ALIASES={
    "United States of America":"US",
    "Russia":"RU",
    "South Korea":"KR",
    "North Korea":"KP",
    "Vietnam":"VN",
    "Laos":"LA",
    "Iran":"IR",
    "Syria":"SY",
    "Tanzania":"TZ",
    "Bolivia":"BO",
    "Venezuela":"VE",
    "Moldova":"MD",
    "Brunei":"BN",
    "Ivory Coast":"CI",
    "Czechia":"CZ",
    "Democratic Republic of the Congo":"CD",
    "Republic of the Congo":"CG",
    "The Bahamas":"BS",
    "Gambia":"GM",
    "East Timor":"TL"
}

def alpha2(rec):
    lower={str(k).lower():v for k,v in rec.items()}
    for key in ("iso_a2","iso_3166_2","iso_3166_"):
        v=str(lower.get(key) or "").strip()
        if "-" in v and len(v.split("-",1)[0])==2:v=v.split("-",1)[0]
        if len(v)==2 and v!="-99":return v.lower()
    for key in ("adm0_a3","sr_adm0_a3","gu_a3","sov_a3"):
        a3=str(lower.get(key) or "").strip()
        if len(a3)==3 and a3!="-99":
            try:
                return pycountry.countries.lookup(a3).alpha_2.lower()
            except LookupError:
                pass
    for key in ("admin","geonunit","sovereignt"):
        name=str(lower.get(key) or "").strip()
        if not name:continue
        if name in COUNTRY_NAME_ALIASES:return COUNTRY_NAME_ALIASES[name].lower()
        try:
            return pycountry.countries.lookup(name).alpha_2.lower()
        except LookupError:
            pass
    return None

def region_name(rec):
    return str(rec.get("name") or rec.get("name_en") or rec.get("gn_name") or rec.get("iso_3166_2") or "").strip()

def points_to_path(points, parts, minx, miny, scale, pad, height):
    chunks=[]
    starts=list(parts)+[len(points)]
    for a,b in zip(starts,starts[1:]):
        ring=points[a:b]
        if len(ring)<3:continue
        coords=[]
        for x,y in ring:
            sx=pad+(x-minx)*scale
            sy=height-(pad+(y-miny)*scale)
            coords.append((sx,sy))
        chunks.append("M "+" L ".join(f"{x:.2f},{y:.2f}" for x,y in coords)+" Z")
    return " ".join(chunks)

def main():
    if MANIFEST.exists():
        try:
            m=json.loads(MANIFEST.read_text(encoding="utf-8"))
            if m.get("version")==VERSION and len(list(OUT.glob("*.svg")))>=150:
                print("Country subdivision SVG maps already current")
                return
        except Exception:
            pass

    with tempfile.TemporaryDirectory() as td:
        z=Path(td)/"admin1.zip"
        urllib.request.urlretrieve(SOURCE,z)
        with zipfile.ZipFile(z) as archive:
            archive.extractall(td)
        shp=next(Path(td).glob("*.shp"))
        reader=shapefile.Reader(str(shp),encoding="utf-8",encodingErrors="replace")
        print("Natural Earth admin1 fields:", [x[0] for x in reader.fields[1:]])
        first_record=next(reader.iterRecords(),None)
        if first_record is not None:
            print("Natural Earth first record:", first_record.as_dict())
        reader=shapefile.Reader(str(shp),encoding="utf-8",encodingErrors="replace")
        grouped=defaultdict(lambda:defaultdict(list))
        for sr in reader.iterShapeRecords():
            rec=sr.record.as_dict()
            iso=alpha2(rec)
            name=region_name(rec)
            if iso and name and sr.shape.points:
                grouped[iso][name].append(sr.shape)

        generated=0
        for iso,regions in grouped.items():
            allpts=[pt for shapes in regions.values() for s in shapes for pt in s.points]
            if not allpts:continue
            xs=[p[0] for p in allpts]; ys=[p[1] for p in allpts]
            minx,maxx,miny,maxy=min(xs),max(xs),min(ys),max(ys)
            dx=max(maxx-minx,1e-6); dy=max(maxy-miny,1e-6)
            width,height,pad=1000.0,650.0,22.0
            scale=min((width-2*pad)/dx,(height-2*pad)/dy)
            paths=[]
            for name,shapes in sorted(regions.items(),key=lambda x:x[0].casefold()):
                d=" ".join(points_to_path(s.points,s.parts,minx,miny,scale,pad,height) for s in shapes)
                if not d:continue
                paths.append(f'<path id="r-{slug(name)}" data-region="{esc(name)}" d="{d}"/>')
            svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {int(width)} {int(height)}" role="img" aria-label="{iso.upper()} first-level administrative map"><g fill="#e2e3e5" stroke="#fff" stroke-width="1.5" stroke-linejoin="round">{"".join(paths)}</g></svg>'''
            (OUT/f"{iso}.svg").write_text(svg,encoding="utf-8")
            generated+=1

    MANIFEST.write_text(json.dumps({
        "source":"Natural Earth Admin 1 – States, Provinces",
        "sourceUrl":"https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/",
        "download":SOURCE,
        "version":VERSION,
        "license":"Natural Earth public domain / free for use in any type of project",
        "generatedMaps":generated
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Generated subdivision SVG maps={generated}")

if __name__=="__main__":
    main()
