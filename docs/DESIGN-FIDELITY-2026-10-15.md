# DORAPP — design-to-code fidelity contract (2026-10-15)

## Canonical reality
The visual concept is a direction, **not a data or functionality specification**. Production is a Hungarian-language global diaspora directory. The live world map is a repository-owned SVG (assets/world-map.svg), not OpenStreetMap tiles. Its country research statuses and derived organization counts come from data/global.json and the global data model; do not fabricate map pins, country counts, organizations, event cards, or ratings.

## Implemented in PR #32
- Homepage-only additive CSS layer design-editorial.css, loaded after styles.css.
- System UI typography, restrained fluid headings, accessible focus states, calmer surfaces, consistent spacing and responsive geometry.
- Existing IDs and data hooks untouched: globalSearch, globalSearchSuggestions, worldMap, worldMapViewport, worldMapStatus, worldCountryList, organizationDirectory, globalCalendarGrid.
- Existing world.js, ui.js, source status logic, attribution, legal links, consent and event sourcing preserved.

## Mapping from visual concept to canonical UI
- Hero headline: existing 'Magyar közösségek egy helyen.' rather than the unapproved concept headline.
- Map: actual interactive world SVG with reviewed/researching/unresearched state colors, zoom, pan and country selection; no fictional location markers.
- Search: actual suggestion index of verified country datasets; do not add nonfunctional category pills.
- Organizations: real directory with country/type/text filters, verified leaf-page links and incremental pagination.
- Events: real global calendar with country/text filters, verified event sources; no mock listings.
- Footer: existing publisher, project authorship and source/privacy links.
- Mobile: same data and interactions; no fake bottom tabs or unsupported save/favorite controls.

## Follow-up release gates
1. Validate browser render at 320, 390, 768, 1024, 1440, 1920 and 2560px; ensure no horizontal overflow or broken SVG object interaction.
2. Test keyboard search suggestions, focus, world map zoom/pan and touch handling, directory and calendar filtering, mobile navigation.
3. Confirm no analytics before consent; validate SEO/JSON-LD unchanged.
4. Verify CI, review PR and merge only after checks; then confirm exact live deployment.

## Design tokens
Text #1d1d1f; secondary #6e6e73; background #fff; section surface #f5f5f7; accent #245a81; border #e5e5e7. System font stack, no redistribution of Apple's SF Pro fonts.
