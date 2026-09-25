# DORAPP Profile Steward

Ez a dokumentum a szervezeti profilok forrásalapú bővítésének szabályait rögzíti.

## Munkamegosztás

- A napi GitHub curator automatikusan frissíti az eseményeket és a szervezethez kapcsolható sajtó-/háttéranyag-indexet.
- A strukturált profilmezőket ChatGPT/Work steward vagy emberi szerkesztő bővíti.
- A steward kizárólag ellenőrzött, megnyitott forrás alapján írhat történeti vagy szervezeti tényt.

## Bővíthető profilmezők

- `founded`
- `history.summary`
- `history.milestones[]`
- `activities[]`
- `targetGroups[]`
- `languages[]`
- `email`
- `phone`
- `profileVerifiedAt`

### history.milestones

Ajánlott forma:

```json
{
  "date": "1980-02-09",
  "title": "Megalakulás",
  "description": "Rövid, tényszerű leírás.",
  "sourceUrl": "https://..."
}
```

A `date` helyett `year` is használható, ha csak az év bizonyítható.

## Forrásprioritás

1. hivatalos szervezeti weboldal
2. hivatalos intézményi/ernyőszervezeti oldal
3. ORF Volksgruppen vagy más közszolgálati forrás
4. Rólunk.at, Bécsi Napló és más releváns ausztriai magyar sajtó
5. másodlagos forrás csak akkor, ha nincs jobb elsődleges bizonyíték

## Kötelező szabályok

- Ne találj ki alapítási évet, vezetőt, címet, tevékenységet vagy történeti mérföldkövet.
- Ha az adat nem bizonyítható, maradjon üresen.
- Egy egyszeri eseményt ne írj be állandó tevékenységként.
- A sajtócikkből átvett történeti tényt lehetőleg mérföldkőként, sourceUrl-lal rögzítsd.
- Ha a saját weboldal üres vagy használhatatlan, az aktív hivatalos Facebook/Instagram lehet elsődleges profil-link.
- A formális tagságot, affiliationt és parent-child kapcsolatot ne mosd össze.
- Minden módosítás után futtasd a directory validátort, generáld újra a profilokat és ellenőrizd a production deployt.

## Heti steward audit

A heti audit feladata:

1. új szervezetek és alcsoportok keresése;
2. meglévő profilok hiányzó mezőinek feltöltése;
3. friss sajtómegjelenések átolvasása;
4. bizonyított történeti adatok és mérföldkövek kinyerése;
5. tevékenységek és célcsoportok pontosítása;
6. kontaktadatok és közösségi linkek ellenőrzése;
7. üres vagy elavult weboldalak helyett aktív hivatalos közösségi link használata;
8. validáció, commit, deploy, production visszaellenőrzés.

## Amit a napi automatika nem csinál

A napi curator nem ír át `intro`, `history`, `activities`, `targetGroups`, `founded`, `email` vagy `phone` mezőt. Ezek csak forrásalapú steward szerkesztéssel változhatnak.
