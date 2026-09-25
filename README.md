# DORAPP — Magyar Programok Ausztriában

Országos, forrásalapú ausztriai magyar szervezeti és eseményplatform.

## Cél

Egyetlen kereshető felületre hozza az Ausztriában működő magyar egyesületeket, civileket, oktatási és kulturális szervezőket, közösségeket és nyilvános eseményeiket.

## Jelenlegi lefedettség

- 9 osztrák tartomány
- 77 szervezet, civil közösség, kulturális intézmény, médiafelület és programgazda
- tartományi térképes kezdőlap
- kereshető szervezeti adatbázis
- szervezeti bemutatkozó profilok
- országos eseménynaptár
- Google Maps és Apple Maps útvonaltervezés igazolt cím esetén
- napi automatikus eseményforrás-ellenőrzés, forrásonkénti állapotnaplóval

## Architektúra

A projekt három korábbi rendszer legerősebb elemeit egyesíti:

- **okoszisztema** → forrásbizonyíték, authority, GEO/LLM/AI Trust
- **BMIPROGRAM** → programkereső, helyszín, esemény- és útvonallogika
- **BMITANAROK** → kereshető bemutatkozó/profilmodell

A DORAPP saját, országos adatmodellre épül, BMI-specifikus függés nélkül.

## Adatok

- `data/organizations.json` — szervezetek, város, tartomány, bemutatkozás, web/social és eseményforrások
- `data/events.json` — forrásból igazolt események
- `data/source-health.json` — napi forrásellenőrzés állapota
- `data/discovery-sources.json` — országos felderítő és háttérforrások (ORF, Rólunk.at, KCSP, Bécsi Napló)

## Napi curator

`.github/workflows/austria-hungarian-program-curator.yml`

Naponta:
1. bejárja a rögzített eseményforrásokat;
2. Schema.org Event JSON-LD-t keres;
3. azonos domainen esemény/program linkeket követ;
4. ICS / VEVENT forrásokat feldolgoz;
5. megőrzi a forrás URL-t és ellenőrzési időt;
6. validálja az adatkapcsolatokat;
7. csak forrásalapú változást commitol.

A rendszer nem talál ki hiányzó dátumot, helyszínt vagy szervezői kapcsolatot.

## Production

Statikus frontend. GitHub Pages deployment a `.github/workflows/deploy-pages.yml` workflow-val.

Production domain még nincs rögzítve; canonical/sitemap csak a végleges domain kiválasztása után kerül be.


## Regionális együttműködési hálók

A DORAPP külön kezeli a formális ernyőszervezeti tagságot és a dokumentált regionális együttműködést.

- **Ernyőszervezeti tagság**: csak név szerint igazolt tagság kerül be.
- **Regionális háló**: együttműködő szervezetek kapcsolata, amely nem jelent automatikusan tagsági vagy jogi alárendeltséget.

Első ilyen háló: **Burgenlandi magyar együttműködési háló**, a Burgenlandi Magyar Kultúregyesület (BMKE) körül.
