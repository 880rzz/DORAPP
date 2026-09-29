#!/usr/bin/env python3
"""Build the non-destructive global compatibility layer.

Austria remains canonical in data/*.json during migration. This script mirrors
those files into data/countries/at/ and derives data/global.json. No source data
is edited by this generator.
"""
import json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
COUNTRY_DIR=DATA/"countries"/"at"
SOURCE_FILES=("organizations.json","events.json","education.json","source-health.json","articles.json","discovery-sources.json")

COUNTRY_DIR.mkdir(parents=True,exist_ok=True)
for name in SOURCE_FILES:
    src=DATA/name
    if src.exists():
        shutil.copyfile(src,COUNTRY_DIR/name)

orgdb=json.loads((DATA/"organizations.json").read_text(encoding="utf-8"))
evdb=json.loads((DATA/"events.json").read_text(encoding="utf-8"))
edudb=json.loads((DATA/"education.json").read_text(encoding="utf-8"))

entity_count=len(orgdb.get("organizations",[]))
organization_count=sum(1 for o in orgdb.get("organizations",[]) if o.get("entityClass")!="activity")
activity_count=entity_count-organization_count
event_count=len(evdb.get("events",[]))
education_count=len(edudb.get("institutions",edudb.get("education",edudb.get("items",[]))))

global_db={
  "schemaVersion":1,
  "countPolicy":"organizationCount excludes entityClass=activity; all counts are generated from canonical country data",
  "countries":[{
    "iso2":"at","iso3":"AUT",
    "name":{"hu":"Ausztria","de":"Österreich","en":"Austria"},
    "locales":["de-AT","hu"],
    "researchStatus":"reviewed",
    "canonicalDataMode":"legacy-compatibility-mirror",
    "canonicalLegacyPaths":{"organizations":"data/organizations.json","events":"data/events.json","education":"data/education.json"},
    "countryDataPath":"data/countries/at/",
    "route":"countries/at/",
    "counts":{"organizations":organization_count,"activities":activity_count,"entities":entity_count,"events":event_count,"education":education_count}
  }]
}
(DATA/"global.json").write_text(json.dumps(global_db,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"Global compatibility layer: AT organizations={organization_count}, activities={activity_count}, events={event_count}, education={education_count}")
