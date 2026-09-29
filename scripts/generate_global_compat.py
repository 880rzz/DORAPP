#!/usr/bin/env python3
"""Build the non-destructive worldwide country registry and Austria mirror."""
import json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
AT=DATA/"countries"/"at"
SOURCE_FILES=("organizations.json","events.json","education.json","source-health.json","articles.json","discovery-sources.json")
ISO2_CODES="""ad ae af ag ai al am ao aq ar as at au aw ax az ba bb bd be bf bg bh bi bj bl bm bn bo bq br bs bt bv bw by bz ca cc cd cf cg ch ci ck cl cm cn co cr cu cv cw cx cy cz de dj dk dm do dz ec ee eg eh er es et fi fj fk fm fo fr ga gb gd ge gf gg gh gi gl gm gn gp gq gr gs gt gu gw gy hk hm hn hr ht hu id ie il im in io iq ir is it je jm jo jp ke kg kh ki km kn kp kr kw ky kz la lb lc li lk lr ls lt lu lv ly ma mc md me mf mg mh mk ml mm mn mo mp mq mr ms mt mu mv mw mx my mz na nc ne nf ng ni nl no np nr nu nz om pa pe pf pg ph pk pl pm pn pr ps pt pw py qa re ro rs ru rw sa sb sc sd se sg sh si sj sk sl sm sn so sr ss st sv sx sy sz tc td tf tg th tj tk tl tm tn to tr tt tv tw tz ua ug um us uy uz va vc ve vg vi vn vu wf ws ye yt za zm zw""".split()

AT.mkdir(parents=True,exist_ok=True)
for name in SOURCE_FILES:
    src=DATA/name
    if src.exists(): shutil.copyfile(src,AT/name)

orgdb=json.loads((DATA/"organizations.json").read_text(encoding="utf-8"))
evdb=json.loads((DATA/"events.json").read_text(encoding="utf-8"))
edudb=json.loads((DATA/"education.json").read_text(encoding="utf-8"))
entity_count=len(orgdb.get("organizations",[]))
organization_count=sum(1 for o in orgdb.get("organizations",[]) if o.get("entityClass")!="activity")
activity_count=entity_count-organization_count
event_count=len(evdb.get("events",[]))
education_count=len(edudb.get("institutions",edudb.get("education",edudb.get("items",[]))))

countries=[]
for iso in ISO2_CODES:
    (DATA/"countries"/iso).mkdir(parents=True,exist_ok=True)
    countries.append({
      "iso2":iso,
      "name":{"en":iso.upper()},
      "researchStatus":"unresearched",
      "countryDataPath":f"data/countries/{iso}/",
      "route":f"countries/{iso}/",
      "counts":{"organizations":0,"activities":0,"entities":0,"events":0,"education":0}
    })

countries[ISO2_CODES.index("at")]={
    "iso2":"at","iso3":"AUT",
    "name":{"hu":"Ausztria","de":"Österreich","en":"Austria"},
    "locales":["de-AT","hu"],
    "researchStatus":"reviewed",
    "canonicalDataMode":"legacy-compatibility-mirror",
    "canonicalLegacyPaths":{"organizations":"data/organizations.json","events":"data/events.json","education":"data/education.json"},
    "countryDataPath":"data/countries/at/","route":"countries/at/",
    "counts":{"organizations":organization_count,"activities":activity_count,"entities":entity_count,"events":event_count,"education":education_count}
}
global_db={
  "schemaVersion":1,
  "countryCodeStandard":"ISO 3166-1 alpha-2",
  "countryUniverseSize":len(countries),
  "countPolicy":"organizationCount excludes entityClass=activity; all counts are generated from canonical country data",
  "countries":countries
}
(DATA/"global.json").write_text(json.dumps(global_db,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"Global registry: {len(countries)} ISO entries; AT organizations={organization_count}, activities={activity_count}, events={event_count}, education={education_count}")
