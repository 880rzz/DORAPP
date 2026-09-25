# DORAPP — Magyar Programok Ausztriában

Országos, forrásalapú ausztriai magyar szervezeti és eseményplatform.

## Cél

Egyetlen kereshető felületre hozza az Ausztriában működő magyar egyesületeket, civileket, oktatási és kulturális szervezőket, közösségeket és nyilvános eseményeiket.

## Jelenlegi lefedettség

- 9 osztrák tartomány
- 70 szervezet / programgazda
- tartományi térképes kezdőlap
- kereshető szervezeti adatbázis
- szervezeti bemutatkozó profilok
- országos eseménynaptár
- Google Maps és Apple Maps útvonaltervezés igazolt cím esetén
- napi automatikus eseményforrás-ellenőrzés

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
