# DORAPP tartalmi és cellaméret-szabály

Ez a szabály minden kézzel írt és generált DORAPP-oldalra érvényes.

## Azonos méretű elemek

- Azonos listában vagy rácsban azonos típusú kártyák és cellák azonos méretűek.
- A rácsok `minmax(0, 1fr)` oszlopokat és egységes automatikus sormagasságot használnak.
- A cella közvetlen gyermekei `min-width: 0` értéket kapnak.
- Név, URL, e-mail-cím és leírás nem növelheti meg önkényesen a cellát, és nem lóghat ki belőle.
- A teljes adat az adatlapon mindig megmarad. A listanézet legfeljebb két soros címet és legfeljebb négy soros leírást mutat.
- Billentyűzettel elérhető fókuszállapot és a teljes értéket megőrző adatlap nélkül tilos pusztán levágni fontos információt.

## Érthető rövid címkék

Csak a felületi címkék rövidíthetők. Szervezet-, személy- és eseménynév csak igazolt, hivatalos rövid névvel rövidíthető.

| Hosszú felületi címke | Rövid címke |
| --- | --- |
| Amerikai Egyesült Államok | USA |
| közösségi szervezet | Közösség |
| oktatási intézmény | Oktatás |
| egyházi közösség | Egyház |
| közösségi média | Közösségi oldal |
| szakmai és gazdasági szervezet | Szakmai / gazdasági |

A rövidítés nem írhatja át a canonical adatot. A teljes megnevezés az adatlapon, az akadálymentes névben vagy szükség esetén a `title` attribútumban marad elérhető.

## Emberi nyelvezet

- A látogatói szöveg rövid, természetes és konkrét magyar mondatokat használ.
- Belső fejlesztői szavak, például `legacy`, `parity`, `ingestion`, `host-institution`, `activity rekord` vagy `steward audit` nem jelenhetnek meg a felületen.
- Hiányzó adatot nem fedünk el általános marketingmondattal.
- A technikai státusz és a szervezet működési státusza külön fogalom.
- A személyes szerzői hang csak kifejezett jogosultsággal és ellenőrizhető forrásból elemezhető; hozzáférés nélkül stílusprofilt tilos kitalálni.

## Automatizált ellenőrzés

A napi workflow ellenőrzi a belső linkeket és horgonyokat, a külső linkek technikai állapotát, a profil-lefedettséget, a kötelező bizonyítékokat és a látogatói zsargont. Külső 403, 429, TLS-, DNS- vagy timeout-hiba önmagában nem törlési ok.

Az eseményforrások frissítése az ütemezett napi futásban és a kézzel indított teljes futásban történik. A pusztán kódváltozás miatt induló ellenőrzés alapértelmezésben nem olvassa újra az eseményforrásokat.
