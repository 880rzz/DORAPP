# DORAPP — design-to-code fidelity contract (2026-10-15)

## Canonical reality

The visual concept is a direction, not a data or functionality specification. Production is a Hungarian-language global diaspora directory. The live world map is the repository-owned `assets/world-map.svg`; country research states and organization counts come from canonical data. Do not fabricate pins, counts, organizations, events or ratings.

## Implemented in PR #32

- One additive and reversible `design-editorial.css` layer, loaded after `styles.css` on every public page family.
- Exact design tokens: text `#1d1d1f`, secondary `#6e6e73`, background `#fff`, surface `#f5f5f7`, accent `#245a81`, border `#e5e5e7`, maximum content width 1280px.
- System UI typography with no bundled Apple fonts, restrained fixed breakpoint sizes, zero negative letter spacing, consistent spacing and focus states.
- Shared editorial treatment for the homepage, country routes, organization, education and event profiles, category/state pages, methodology, data quality, header, navigation and footer.
- Existing IDs, data hooks, maps, search, filters, schema, source evidence, consent and AI Trust surfaces remain authoritative.
- Compact gray WhatsApp contact control remains available without an SDK, iframe or pre-click Meta request.

## Mapping from visual concept to canonical UI

- Hero: existing factual page names and summaries, not campaign copy.
- Map: actual interactive SVG with reviewed/researching states, zoom, pan, touch and country selection.
- Search: actual verified index and keyboard suggestions; no fake category controls.
- Organizations and education: real filters and profile links.
- Events: real source-backed calendar records.
- Footer: existing publisher, project authorship, correction contact and privacy links.
- Mobile: the same data and interactions with a responsive navigation and accessible controls.

## Automated release gates

The pull-request workflow regenerates every public page family, validates canonical, SEO, Schema and GDPR invariants, then runs Chromium at 13 required widths: 320, 375, 390, 621, 768, 1024, 1180, 1280, 1440, 1600, 1920, 2560 and 3840 px.

Representative routes cover the homepage, country page, legacy and global organization profiles, education, events, categories, states, methodology and data quality. The audit fails on missing editorial CSS, horizontal overflow, clipped headings or controls, broken header/footer/main structure, search keyboard regressions, filter empty/reset regressions, map zoom failures, mobile navigation failures or analytics loading before consent.

The workflow also produces screenshots and measured Lighthouse reports as artifacts. The homepage release floor is 0.75 performance; the data-heavy Austria country route has a 0.65 performance regression floor; accessibility, best-practices and SEO must reach 0.90 on both. Merge is allowed only after the repository validators, browser matrix and these measured route-specific Lighthouse thresholds pass.
