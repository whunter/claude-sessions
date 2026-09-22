# Spec: Make duplicate Archive titles unique for SEO

## Problem Statement

The public-facing Archive site serves many records whose `title` is identical to one or more other records — e.g. multiple carved arrowheads or multiple insects of the same species, each cataloged separately but sharing one descriptive title. Duplicate titles across pages hurt SEO. Some of these are legitimate (genuinely distinct physical items that happen to share a description); a smaller number are coincidental collisions between records in entirely unrelated collections.

## Solution

Extend `archive-title-dedup` (currently a report-only scanner) with two new commands, `apply` and `rollback`, so that duplicate titles within a given collection can be made unique by appending a human-curated label and the record's own catalog identifier, and so that any such change can be precisely undone.

The work is done one collection at a time, deliberately — collections differ enough in what an appropriate distinguishing label looks like ("Map", "Specimen", "Photo", etc.) that no single automatic rule fits all of them. A collection is only touched once someone has decided what its label should be.

## User Stories

1. As the archive maintainer, I want to scan the Archive table and get a JSON report of every title shared by 2+ records, so that I know the scope of the duplication problem.
2. As the archive maintainer, I want to pick one collection out of that report and assign it a short human-readable suffix label (e.g. "Map"), so that I control what the disambiguating text looks like per collection.
3. As the archive maintainer, I want to run `apply` scoped to exactly one collection at a time, so that I never accidentally rewrite titles across collections I haven't reviewed yet.
4. As the archive maintainer, I want collections I haven't assigned a label to be silently left untouched by `apply`, so that "not yet configured" naturally means "not yet touched" without a separate exclusion list.
5. As the archive maintainer, I want each duplicate record's new title to be `<original title> - <suffix>:<identifier>` using its own full catalog identifier, so that every rewritten title is guaranteed unique without needing any cross-record coordination or ordering.
6. As the archive maintainer, I want records that collide on title purely by coincidence across two different collections to be treated independently by their own collection's label, so that I don't need special-case logic for that overlap.
7. As the archive maintainer, I want to pass `-collection_identifier` and `-suffix` as CLI flags on `apply`, so that the target of a specific run is always explicit in the command itself rather than hidden in an easy-to-forget config file edit.
8. As the archive maintainer, I want `apply` to fall back to `config.yaml` values for `collection_identifier`/`suffix` when the flags are omitted, so that I'm not forced to always type them.
9. As the archive maintainer, I want a `-dry-run` mode on `apply` that logs every planned old→new title change verbosely without writing anything, so that I can sanity-check a collection's suffix and identifier formatting before committing to a live write.
10. As the archive maintainer, I want `apply` to always compute the new title from the *original* title recorded in the input report JSON (not from whatever is currently in DynamoDB), so that re-running `apply` with the same input/collection/suffix is safe and idempotent rather than compounding suffixes.
11. As the archive maintainer, I want every real (non-dry-run) `apply` run to write its own change-log file — named with the collection identifier and a timestamp — recording exactly which records it wrote and their old/new titles, so that I have a precise, run-scoped record independent of the original scan.
12. As the archive maintainer, I want to run `rollback` against either the original report JSON or a specific run's change-log, so that I have one recovery path regardless of which file I have on hand.
13. As the archive maintainer, I want `rollback` to unconditionally restore each listed record's `title` to the original recorded in the given file, so that recovery is simple and predictable even if I don't remember the current state of the record.
14. As the archive maintainer, I want `rollback`'s only safety gate to be that it operates on an explicit input file, matching `apply`'s dry-run-as-sufficient-gate philosophy, so that neither command requires an extra confirmation flag beyond deliberately supplying the right input and choosing not to dry-run.

## Implementation Decisions

- **New commands**: `apply` and `rollback`, alongside the existing `report` command.
- **`apply` flags**: `-collection_identifier`, `-suffix`, `-input <report-or-changelog.json>`, `-dry-run`, `-config config.yaml`. `collection_identifier` and `suffix` fall back to `config.yaml` fields of the same name when not passed as flags.
- **Seam**: a single pure planning function, `planApply(report Report, collectionIdentifier, suffix string) []Job`, where `Job` is `{Identifier, OldTitle, NewTitle}`. It takes the parsed input JSON and the two resolved values and returns the full list of writes with no AWS or file I/O. All DynamoDB `UpdateItem` calls and file I/O are thin glue around this function.
- **Filtering**: `apply` reads the full input JSON (which may span many collections, as produced by `report`), and `planApply` selects only records whose `parent_collection` equals `collectionIdentifier`. No group-level (title-group) logic — every matching record is planned independently by its own `parent_collection` and `identifier`, including records that belong to a title-group whose other members are in a different collection.
- **New-title format**: `<original title> - <suffix>:<identifier>`, where `identifier` is the record's full, unmodified `identifier` field.
- **Write target**: `title` is overwritten in place in DynamoDB (not a new/parallel field). No other system (search index, cache, static rebuild) needs to be refreshed — DynamoDB is the only downstream dependency.
- **Idempotency source of truth**: the *input JSON's* recorded title is always treated as the original for computing the new title, regardless of what `title` currently holds in DynamoDB. This is what makes repeated `apply` runs against the same input/collection/suffix safe.
- **Change-log**: on a real (non-dry-run) `apply` run, a change-log file is written using the same `title → records` JSON shape as the `report` output, plus `collection_identifier` and a timestamp embedded in the filename (e.g. `changelog_<collection_identifier>_<timestamp>.json`). This shared shape is what lets `rollback` accept either an original report or a change-log through one code path.
- **`rollback <file>`**: reads a file in the report/change-log shape, and for every record listed, writes `title` back to that file's recorded value — unconditionally, with no check against the record's current live value.
- **Dry-run as the only gate**: neither `apply` nor `rollback` requires a separate `-confirm`/`-yes` flag or interactive prompt. `-dry-run` (on `apply`) is the sole preview mechanism; choosing not to pass it is a deliberate, sufficient signal to write for real.
- **Config**: `config.yaml` keeps its existing fields (`region`, `table_name`, `output_dir`, `output_file`, `concurrency`) and gains optional `collection_identifier` / `suffix` fields used only as fallback defaults for `apply`'s flags.

## Testing Decisions

- Good tests here exercise `planApply` and `planRollback` as pure functions: given an input `Report`/change-log struct and a `collection_identifier`/`suffix`, assert on the resulting `[]Job` — not on DynamoDB calls or file contents. This mirrors the existing style of testing `findDuplicates`'s grouping logic directly rather than mocking the AWS SDK.
- Cases to cover for `planApply`: records in the target collection are included; records in other collections are excluded; a title-group whose records span two collections only contributes the records matching the target collection; the computed `NewTitle` format matches `<title> - <suffix>:<identifier>` exactly; re-planning the same input twice produces identical jobs (idempotency).
- Cases to cover for `planRollback`: given a report or a change-log shaped file, the resulting jobs restore each record's original title; a file containing records is not otherwise filtered (all listed records are planned).
- The DynamoDB write path (`UpdateItem` calls) and file I/O (reading input JSON, writing the change-log) are thin and are exercised via dry-run/manual runs against the dev table, consistent with how `scanSegment`'s live AWS calls are handled today (not unit-tested against a mock).

## Out of Scope

- Sequential/counter-based suffixes (rejected in favor of using the record's own identifier).
- Per-item-category filtering logic (rejected — every matching record in the target collection is planned independently).
- Any special-casing for title-groups that span multiple collections (handled naturally by per-record, per-collection planning).
- Writing to a separate `display_title` field instead of `title`.
- Refreshing any downstream system other than DynamoDB (no search index or cache in this pipeline).
- A required `-confirm`/interactive-prompt gate beyond `-dry-run`.
- State verification in `rollback` (e.g. refusing to revert a record whose current title doesn't match what's expected) — explicitly rejected; rollback always writes the recorded original.

## Further Notes

- An earlier iteration of this tool (commits `f734ac3` through `4817ce1` in this repo's history) already built a similar write path — with a sequential-counter suffix, item-category filtering, and a rollback/change-log — before being deliberately stripped back to a report-only scanner (`f88fae1`). This spec supersedes that earlier design; do not resurrect the counter-based suffix or category-filter logic from it.
- As of the last `report` run, the table had 451 duplicate-title groups across 13 distinct `parent_collection` values, with 11 groups spanning more than one collection (coincidental title collisions, not the same-physical-object case this feature targets).
- `config.yaml`'s `table_name` currently points at what appears to be a dev table; this spec makes no distinction between dev/prod in code — whichever table `config.yaml` names is what every command operates against.
