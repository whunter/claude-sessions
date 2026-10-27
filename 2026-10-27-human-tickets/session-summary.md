# Session summary: rewriting the wayfinder tickets for humans

**Date:** 2026-10-27 (the session began earlier and carried across a context compaction)
**Repo:** `dlp-access-next`, branch `tickets`, `acf6cca`..`94485ab` for the final part, 38 commits over `main` in total

## Goal

Rename `docs/wayfinder/tickets` to `claude-tickets`. Then rewrite each ticket for a human reader in `docs/wayfinder/tickets/`, splitting broad ones into vertical-slice sub-tickets. One sub-agent handled each ticket, one at a time, and the owner checked in after each ticket. Writing only: no code was copied or written.

## What was produced

- **01–03** (inventories: public data, styling, viewer compatibility): resolved. They hold the styling and caching decisions.
- **04 typed query layer** (04a–04g): site, item, collection, collection items with 12 sort fields, sub-collection tree via CDK `getCollectionMap`, search and browse, page content and metadata.
- **05 styling** (05a–05f): one global stylesheet plus CSS Modules, tree and carousel libraries, modal, icon set, vt-fonts.
- **06 viewers** (06a–06f): media dispatch and PDF, latest Mirador, Babylon glTF with the environment taken from the record, 3D/2D toggle, Minerva, image/audio/video. x3dom, mtl, obj and kaltura are dropped.
- **07 layout** (07a–07h): header, mobile drawer, breadcrumbs, footer web component, head tags and production-only analytics, error pages, cookie consent, structured data.
- **08 parity tests** (08a–08f): Cypress and Jest, with CI through CDK. Nothing is tested against the old site.
- **09 item routing** (09a–09d): Items are served at both `/item/:key` and `/archive/:key` with no redirect. This is ADR 0002 (Proposed), which supersedes ADR 0001.
- **10 live data checks** (10a–10d): run against dev only. Findings go to `docs/research/live-data-checks.md`.
- **11 media URLs** (11a–11c): everything is public, served by CloudFront in front of a new S3 storage stack, never direct S3. The URL suffix varies by environment.
- **12 item location map**: the Location card, using Leaflet and OpenStreetMap. It was moved out of the viewer tickets because maps are otherwise tiled images in Mirador.
- **13 public pages** (13a–13i): browse, home, collection, search results and facets, site pages, metadata guide, feedback. The new URLs are `/browse/collections`, `/about`, `/about/permissions`, `/about/metadata` and `/about/<slug>`. Site page HTML is always sanitized (`allowScripts` dropped).
- **cdk-requests.md**: C1–C10 (storage stack, media base URL and SITE_ID per environment, getCollectionMap, Babylon skybox field, GitHub CI AWS permissions, dev data read access, merging the CDK deployment branch, hierarchy_path mapping, search filter fields, feedback endpoint).
- **map.md**: rewritten as the index for all of the above.

## Final steps this session

- `abee9c8`: recorded the owner's page decisions and added C10. No Item or Collection URL conflicts were found on the feature branches. The 4 added sort fields need no CDK work.
- `86c8d8d`: rewrote map.md. All links resolve, and all 66 tickets are linked.
- `94485ab`: fixed stale "Blocked by" lines in 07h and 08c, and removed the dropped `archived` filter request from 04 and cdk-requests.md.

## Deferred

See handoff.md, "Next steps".
