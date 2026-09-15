# IAWA Meta Export — Hand-off

## Current state

- All CSVs in `/Users/whunter/dev/dlp/assets/iawa/meta/collection_exports/` (24 files) have `createdAt`, `updatedAt`, and `archived` removed — each now has 8 columns: `relation, identifier, visibility, rights_statement, related_url, description, rights, title`.
- `/Users/whunter/dev/dlp/assets/iawa/meta/iawa_collections.csv` has been reduced to the same 8 columns, same order, so it can be diffed/merged/compared directly against the per-collection export files.
- `/Users/whunter/dev/dlp/assets/iawa/meta/iawa_archives.csv` (3,369 rows) trimmed to 26 columns: `belongs_to, bibliographic_citation, circa, contributor, coverage, create_date, creator, description, display_date, end_date, format, identifier, is_part_of, language, location, medium, modified_date, resource_type, rights, rights_holder, rights_statement, source, spatial, start_date, tags, title, type`.
- All 24 CSVs in `/Users/whunter/dev/dlp/assets/iawa/meta/archive_exports/` trimmed/reordered to match `iawa_archives.csv`'s column set (each file only keeps the subset of those columns it originally had — no backfilling).
- Verified: every row in `archive_exports/*.csv` matches `iawa_archives.csv` by `identifier` with zero mismatches; `iawa_archives.csv` has no duplicate identifiers.

## Untouched, no action needed

- `20250325_Feuerstein_Ms2007_007_box1_archive_metadata.csv`, `LeviseurElsa_Ms1990_007_archive_metadata.csv`, `LeviseurElsa_Ms1990_007_single_archive_metadata.csv`, `manifest.json`, `top.json` — not touched, out of scope.

## To resume

No open work items from this session. All CSVs in `collection_exports/`, `archive_exports/`, `iawa_collections.csv`, and `iawa_archives.csv` are now column-normalized and cross-verified. If further work is needed (e.g. normalizing the remaining standalone metadata CSVs listed above), that would be a new task.
