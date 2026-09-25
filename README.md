# DORAPP — Magyar Programok Ausztriában

Országos, forrásalapú ausztriai magyar szervezeti és eseményplatform.

## Cél

Egyetlen kereshető felületre hozza az Ausztriában működő magyar egyesületeket, civileket, oktatási és kulturális szervezőket, közösségeket és nyilvános eseményeiket.

## Jelenlegi lefedettség

- 9 osztrák tartomány
- 97 szervezet, civil közösség, kulturális intézmény, médiafelület, néptánc-/népzenei csoport és programgazda
- 99 oktatási intézmény/helyszín és rendszeres magyar képzési program a bölcsődétől a felsőoktatásig
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
- `data/education.json` — magyar oktatási helyek és képzések
- `data/education-site-health.json` — az oktatási weboldalak rendszeres tartalom- és elérhetőségi auditja
- `data/articles.json` — szervezeti cikk- és háttéranyag-index

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

Production domain: `https://diaszpora.kozpontiszovetseg.at`.

A canonical URL-ek, sitemap, robots és GitHub Pages CNAME ezt a domaint használják.


## Regionális együttműködési hálók

A DORAPP külön kezeli a formális ernyőszervezeti tagságot és a dokumentált regionális együttműködést.

- **Ernyőszervezeti tagság**: csak név szerint igazolt tagság kerül be.
- **Regionális háló**: együttműködő szervezetek kapcsolata, amely nem jelent automatikusan tagsági vagy jogi alárendeltséget.

Első ilyen háló: **Burgenlandi magyar együttműködési háló**, a Burgenlandi Magyar Kultúregyesület (BMKE) körül.


## Oktatási webaudit

`.github/workflows/education-site-audit.yml`

Az oktatási réteg külön futó ellenőrzést kapott. Az audit:
1. megnyitja a rögzített intézményi weboldalt;
2. releváns belső oldalakat is bejár;
3. magyar, kétnyelvű, elsőnyelvi és népcsoporti tartalmat keres;
4. külön jelzi, ha az oldal elérhető, de a magyar program csak külső hiteles forrásból igazolható;
5. nem következtet egy intézményre pusztán a település alapján.

A statikus oktatási profilokat a `scripts/generate_education_profiles.py` generálja.


## Néptánc és népzene

A közösségi adatmodell külön `neptanc` és `nepzene` kategóriát kezel. Az önállóan azonosítható csoportok külön profilt kaphatnak, miközben a `parentOrganizationId` megőrzi a kapcsolatot a fenntartó vagy szülőegyesülettel.
