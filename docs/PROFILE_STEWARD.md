# DORAPP profile steward

This document governs source-backed enrichment of organization profiles.

## Authority

A steward changes canonical JSON, never generated profile HTML. Every material claim needs an opened official, institutional, registry or reliable editorial source. Empty is better than wrong.

## Supported profile fields

Core identity and contact:

- `name`, `aliases[]`, `type`, `categories[]`;
- `city`, `state`/`region`, `address`, `serviceLocations[]`;
- `website`, `facebook`, `instagram`, `publicChannels[]`;
- `email`, `phone`, `contactUrl`;
- `people[]` with public name, role, status and source URL;
- `profileVerifiedAt`.

Editorial detail:

- `founded`;
- `history.summary`, `history.milestones[]`;
- `activities[]`, `targetGroups[]`, `languages[]`;
- `evidenceSources[]`, `calendarSources[]`, `eventSources[]`.

Relationships:

- `parentOrganizationId`: actual organizational unit or owned program;
- `memberships[]`: proven formal membership;
- `affiliations[]`: documented operational, publisher, partner or umbrella relationship;
- `operatedBy`: evidenced external operator.

Never convert these relationship types without evidence.

## People

Publish only officially public professional roles:

```json
{
  "name": "Public name",
  "role": "verified public role",
  "status": "publicly-verified",
  "sourceUrl": "https://official.example/contact"
}
```

Do not publish private contact details or infer employment, governance or ownership from event participation.

## Evidence and sources

Priority: own official site; official registry/institution/umbrella; official social channel; public-service or reliable diaspora media. Search snippets are discovery only.

A broken or obsolete domain must not outrank an active official social page. Technical 403/429/timeout/TLS/DNS states are not proof that an organization ceased.

## Automation boundary

Daily automation may refresh events, articles, source health and deterministic derived output. It must not invent or silently overwrite steward-maintained identity, history, contact, people or relationship fields.

## Required completion chain

1. update canonical data;
2. validate identifiers, taxonomy and relationships;
3. regenerate profiles/reference pages/sitemaps;
4. validate static output, JSON-LD, consent and duplicates;
5. inspect the exact diff;
6. commit to `main`;
7. verify Actions, Pages deployment and representative live URLs.
