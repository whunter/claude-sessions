# Session Summary: archive-title-dedup — apply & rollback

**Date:** 2026-09-22
**Repo:** `vtdlp-aws-tools/go/archive-title-dedup`
**Branch:** `fix-duplicates`

## What happened

This session picked up from the earlier report-only rewrite (see the
"2026-09-21 – 2026-09-22" section below) and worked through William H's
original ask — make duplicate titles unique for SEO — from stakeholder
request to a working implementation.

1. **Grilled the request** (`/mattpocock-skills:grill-me` against
   `request_brief.md`) across 6 rounds of questions, resolving:
   - The uniquifying token is each record's own `identifier` (full,
     verbatim), not a synthetic sequential counter.
   - Work proceeds **collection by collection** — a duplicate title's
     suffix label (e.g. "Map", "Photo") is a human judgment call per
     collection, not a single global rule. Fact-finding during the grill
     found 451 duplicate-title groups spanning 13 distinct collections, 11
     of which span more than one collection (coincidental title collisions,
     not "same physical object" cases).
   - `collection_identifier` and `suffix` are CLI flags on `apply`,
     falling back to `config.yaml`.
   - `title` is overwritten in place; the input report JSON's recorded
     title is always the source of truth for "original," making `apply`
     reruns idempotent regardless of DynamoDB's current state.
   - `apply` writes its own per-run change-log (report-shaped JSON, named
     with the collection id + timestamp); `rollback` accepts either a
     report or a change-log and always writes the recorded original,
     unconditionally, with `-dry-run` as the only safety gate (no separate
     confirm flag on either command).
2. **Wrote a spec** (`/mattpocock-skills:to-spec`) — `spec.md` in this
   directory — covering problem statement, 14 user stories, implementation
   decisions, testing decisions, and explicit out-of-scope items (no
   tracker publish; no `mattpocock-skills` setup exists for this project).
   Confirmed the seam with the user first: a single pure planning function
   per command (`planApply`/`planRollback`), no AWS/file I/O, everything
   else is thin glue.
3. **Implemented `apply` and `rollback`** in `main.go`:
   - `Job{Id, Identifier, OldTitle, NewTitle}` plus `planApply`,
     `planRollback`, `writeJobs` (bounded-concurrency `UpdateItem` loop),
     and `buildChangeLog`.
   - Discovered mid-implementation (via `aws dynamodb describe-table`) that
     the table's actual partition key is `id`, a separate UUID from the
     business `identifier` field the scan was already projecting — the old
     `report` projection had no way to target an `UpdateItem` write. Added
     `id` to the scan projection and `Record` struct to fix this.
   - Added `main_test.go` (6 tests) covering the `planApply`/`planRollback`
     seam: collection filtering, mixed-collection groups only including the
     matching-collection records, missing-`parent_collection` records
     skipped, idempotency, and rollback restoring correctly from both a
     change-log (`new_title` present) and a plain report (`new_title`
     absent).
4. Verified `go build`, `go vet`, `go test ./...` all pass, and smoke-tested
   `apply -dry-run` against the real (pre-existing) `duplicate_titles.json`
   — 96 records previewed correctly for one sample collection.
5. Also installed the `modelscope.cn@write-a-prd` skill globally at the
   user's request (unrelated to this tool; blocked once by the auto-mode
   classifier as untrusted code integration, then run manually by the user).

## Key files

- `main.go` — `report` (unchanged logic, now also projects `id`), plus new
  `apply`/`rollback` commands and their supporting types/functions.
- `main_test.go` — new; tests for `planApply`/`planRollback`.
- `../claude-sessions/2026-09-22-title-dedup/spec.md` — full spec produced
  this session.

## Commits (not pushed)

- `2afd9f4` — Add apply and rollback commands for duplicate-title
  disambiguation

(earlier, from the prior session today: `4383202`, `4cf5212`, `f88fae1`,
`f734ac3`, `585c65c` — see git log for full history)

## Not yet done / caveats

- **`output/duplicate_titles.json` is stale** — it predates the `id`
  projection fix, so its records have empty `id` fields. It's fine for
  `-dry-run` but must be regenerated via `report` before any real `apply`
  or `rollback` write.
- No collection has actually been applied against DynamoDB yet — only
  dry-run was exercised.
- No `mattpocock-skills` issue tracker is configured for this project, so
  `spec.md` is a local file only, not published anywhere.
- Nothing pushed to remote per standing instructions; push/PR on request.

## Continuation: collection_identifier field + scoped rollback

Same day, later in the session, the user asked for two follow-up changes to
the `apply`/`rollback` work above.

1. **"Refactor this application so that the collection's identifier field
   is included in the records array entries. `parent_collection` should be
   renamed `collection_id` and store the collection.id, and
   collection.identifier should be written to a `collection_identifier`
   field."**
   - Renamed `Record.ParentCollection` (`json:"parent_collection"`) to
     `Record.CollectionID` (`json:"collection_id"`) — unchanged meaning,
     still the raw DynamoDB collection key from the Archive item's
     `parent_collection` attribute.
   - Added `Record.CollectionIdentifier` (`json:"collection_identifier"`),
     resolved at `report` time from a new `collection_table_name` config
     setting via a new `buildCollectionIndex` scan (id -> identifier map),
     required for `report` (fails fast if unset).
   - **Design decision confirmed with the user first**: `apply`'s
     `-collection_identifier` flag previously matched against the raw
     collection id (a latent naming mismatch — the flag was always called
     `collection_identifier`). Asked whether it should now match the new,
     correctly-named `collection_identifier` field instead of `collection_id`
     — user chose yes. `planApply` and its `Job` struct were updated
     accordingly (`Job` now also carries `CollectionID`/`CollectionIdentifier`
     through to the change-log).
   - Wrote `README.md` for the tool (didn't previously exist) documenting
     config, the report/record JSON shape, and all three commands.
2. **"rollback should be scoped to one collection, just like apply."**
   - `planRollback` gained a `collectionIdentifier` parameter and now skips
     records whose `collection_identifier` doesn't match, exactly like
     `planApply`.
   - `runRollback` gained a `-collection_identifier` flag (falls back to
     `config.yaml`, required — errors out if neither is set), and the
     "no records found" message now names the collection scope.
   - Updated `README.md`'s rollback section and workflow example to match.
3. **"I added a space between the ':' and the `<identifier>` in the
   newTitle format. update the tests to reflect this change."** The user
   edited `main.go` directly (`fmt.Sprintf("%s - %s: %s", ...)`, was
   `"%s - %s:%s"`). Updated `main_test.go`'s expected `NewTitle` values and
   `README.md`'s format description (`<suffix>: <record identifier>`) to
   match; no logic change needed since the seam under test
   (`planApply`/`planRollback`) just echoes whatever format string
   `main.go` builds.
4. **"prepend a timestamp to the filename specified in
   config.yaml:output_file"** — `runReport` now builds the report path as
   `<output_dir>/<timestamp>_<output_file>`, timestamp formatted
   `20060102T150405Z` (UTC), matching the format already used for
   change-log filenames, so successive `report` runs no longer overwrite
   each other. Updated `README.md`'s `report` section, its usage examples,
   and the typical-workflow section to use the timestamped filename.

`main_test.go` was updated for changes 1–3 (new/renamed struct fields in
existing tests, a `TestPlanRollback_SkipsRecordsWithNoCollectionIdentifier`
test, `TestPlanRollback_RestoresRecordedOriginalOnlyForMatchingCollection`
replacing the old regardless-of-collection test, and the colon-space fix).
Change 4 touches only `runReport`'s glue code (no pure seam involved), so no
test changes were needed there. `go build`, `go vet`, and `go test ./...`
pass after each change.

### Commits (not pushed)

- `7e587ac` — Add collection_identifier to report records; rename
  parent_collection to collection_id
- `de754e0` — Add README documenting report/apply/rollback commands
- `ab62635` — Scope rollback to one collection, like apply
- `8322a27` — Add space after colon in disambiguated title suffix
- `1069d98` — Prepend UTC timestamp to report's output_file so runs don't
  overwrite each other

### Not yet done / caveats (continuation)

- Same as above: a fresh, timestamped `duplicate_titles.json` must be
  generated via `report` before any real `apply`/`rollback` — it now also
  needs `collection_table_name` set in `config.yaml`, which wasn't required
  before this continuation.
- No collection has been applied against DynamoDB with the new field names
  or timestamped filenames; only `go test`/`go build`/`go vet` have been
  run, no live AWS smoke test in this continuation.
- Nothing pushed to remote per standing instructions; push/PR on request.

## Continuation 2: revert-legacy for the vtec collection

Same day, a new session. The user had run `apply` against the `vtec`
collection (`-suffix Specimen`) using an older build of this tool from
before `apply`/`rollback` existed, and had no input report or change-log
left to roll back from.

1. **Reconstructed the old algorithm from git history** rather than
   guessing: walked the commits before `2afd9f4` (which introduced the
   current `apply`/`rollback`), specifically `4817ce1` ("Zero-pad title
   index by group size"), and confirmed the old format was
   `<original title><suffix>-<zero-padded index>` (e.g.
   `"Foo: Sample-01"`), with the colon-space living inside the `suffix`
   config value itself, not in the code. This matched the substring the
   user described wanting removed (`": Specimen-<index>"`).
2. **Added a `revert-legacy` command** (`planRevertLegacy`,
   `scanCollectionTitles`, `collectionIDForIdentifier` in `main.go`) that
   works entirely off the live table — no report/change-log input needed.
   It resolves `vtec`'s collection id from the collection table, scans
   `Archive` for records under that collection id, regex-matches each
   live title against `^(.*)<suffix>-\d+$`, and plans restoring the
   captured group. Supports `-dry-run` like the other commands.
3. **Verified before writing**: ran `-dry-run` first (2,239 matches, titles
   all looked correct, e.g. `"Limenitidinae: Specimen-13" ->
   "Limenitidinae"`), confirmed with the user via `AskUserQuestion` before
   the live DynamoDB write (this mutates production-like data with no
   change-log safety net), then ran for real.
4. **Result**: 2,239/2,239 `vtec` records reverted. A follow-up `-dry-run`
   confirms zero remaining matches for that suffix in that collection.
5. Added `TestPlanRevertLegacy_StripsSuffixAndIndex` to `main_test.go` and
   documented `revert-legacy` in `README.md`. `go build`/`go vet`/
   `go test ./...` all pass.

### Key files (continuation 2)

- `main.go` — new `revert-legacy` command, `collectionIDForIdentifier`,
  `scanCollectionTitles`, `legacySuffixPattern`, `planRevertLegacy`.
- `main_test.go` — `TestPlanRevertLegacy_StripsSuffixAndIndex`.
- `README.md` — new `revert-legacy` section.

### Commits (not pushed)

- `26d2062` — Add revert-legacy command to undo pre-apply-era title
  disambiguation

### Not yet done / caveats (continuation 2)

- The 2,239-record `vtec` revert has no change-log of its own — if `vtec`
  needs to be re-disambiguated, use the current `apply` command so a
  proper change-log gets written this time.
- Nothing pushed to remote per standing instructions; push/PR on request.

## Continuation 3: report filename + Markdown collection list

Same day, a new session. Two small changes to `report`:

1. **"Instead of prepending the timestamp to the filename for
   duplicate_titles.json, move the timestamp to the end."** `runReport` now
   splits `output_file` into its name and extension and builds
   `<name>_<timestamp><ext>`, e.g. `duplicate_titles_20260922T153000Z.json`.
   README paths and examples updated to match.
2. **"Create a second output file with the same filename but in markdown.
   Write a list of the identifiers of collections that have existing
   duplicate titles."** `report` now also writes `<name>_<timestamp>.md`
   with a heading and a sorted bullet list of collection identifiers. A
   collection is listed if any of its records is in any duplicate group,
   which matches what `apply -collection_identifier` would change. Records
   with no resolved collection are skipped. Added `duplicateCollections`
   and `collectionsMarkdown` to `main.go`, and `report` prints the count
   and path. README documents the new file.
3. Updated README, `handoff.md`, and this summary.

`go build` and `go vet` pass. `report` was not run against the live table,
and no unit tests were added for the new helpers.

### Commits (not pushed)

- `a0ef2b9` — Append report timestamp to output_file stem instead of
  prepending it
- `cf5e99f` — Write Markdown list of collections with duplicate titles
  alongside report JSON
- `e65aa70` — README: note report's Markdown collection list and
  timestamped filename throughout

### Not yet done / caveats (continuation 3)

- The `.md` output hasn't been checked on a real `report` run yet.
- One open question: should a collection be listed only when two of *its
  own* records share a title? Right now it's also listed when its record
  shares a title with a record in a different collection.
- Nothing pushed to remote per standing instructions; push/PR on request.
