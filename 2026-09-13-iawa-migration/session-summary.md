# Session Summary — iawa-migration (2026-09-13)

## Goal
Investigate the S3 layout of the IAWA IIIF collection `Ms1990_007_Leviseur` and identify ways to simplify its assets.

Target: `s3://vtdlp-pprd.img.cloud.lib.vt.edu/iawa/Ms1990_007_Leviseur/`

## What was done
- Recursively listed the full collection (572,006 objects, ~48.4 GB) and aggregated by extension, folder, and size.
- Compared file structure of a sample item (`Ms1990_007_F001_001_Fleischmann_Dr`) that exists in two places, and diffed `manifest.json` / `canvas/p1.json` between the two copies to confirm they are duplicate content.
- Measured the size of the root-level `tiles/` directory vs. each `Ms1990_007_FolderN/tiles/` directory to confirm the root copy is the deduplicated superset.

## Key findings

**Overall scale:** 572,006 objects, ~48.4 GB. 568,532 JPGs, 3,463 JSON (IIIF manifest/canvas/annotation/sequence docs), 12 CSVs. Only 602 actual page images exist — the JPG count is high because each page is pre-rendered as a static IIIF tile pyramid (~533 tile files/page on average).

**Duplicate content (~21.1 GB, ~44% of total size):** The collection root holds a canonical, merged copy of everything:
- `tiles/` — merged tile pyramid for all 602 pages across all 58 items
- `Ms1990_007_F0XX_..._Dr/{manifest.json, canvas/*.json, annotation/*.json, sequence/default.json}` — per-item IIIF docs referencing the root `tiles/` path
- `collection/top.json` — top-level collection manifest
- `representative.jpg` and two metadata CSVs

In addition, ten subdirectories — `Ms1990_007_Folder1/` through `Ms1990_007_Folder10/` — each contain a **byte-for-byte duplicate** of the tile pyramid and manifest/canvas/annotation/sequence JSON for the items in that folder, plus their own duplicate `collection/top.json`. The only difference from the root copies is that all `@id` URLs point into `.../Ms1990_007_FolderN/...` instead of the root. This was confirmed by diffing `manifest.json` and `canvas/p1.json` between root and `Folder1` — content is identical except for path prefixes. Each `FolderN/` also has a `Ms1990_007_FolderN.csv`, a subset of the main archive metadata CSV.

This pattern strongly suggests each folder's IIIF assets were generated/tiled independently as self-contained batches, then merged into the collection root — but the original per-batch staging directories were never deleted after the merge.

## Recommendation given to the user
1. Before deleting anything, verify no external system (finding-aid records, cached manifest links, etc.) references the `.../Ms1990_007_FolderN/...` manifest URLs specifically rather than the root ones.
2. If clear, delete the 10 `Ms1990_007_FolderN/` directories — reclaims ~21 GB and removes roughly half the object count.
3. Longer-term/architectural note: the static tile-pyramid approach (~533 tiny JPGs/page) is inherently high-object-count. A dynamic IIIF image server (e.g., Cantaloupe/IIPImage) backed by pyramidal TIFF/JP2 masters would reduce this to ~602 master files instead of ~321,000 tile files — a larger infrastructure change, not just an S3 cleanup.

## Status at end of session
Analysis only — no S3 objects were modified or deleted. The user had not yet confirmed whether to proceed with deleting the `Ms1990_007_FolderN/` directories.
