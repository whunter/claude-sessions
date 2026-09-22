# Hand-off: archive-title-dedup

## Where things stand

`vtdlp-aws-tools/go/archive-title-dedup` on branch `fix-duplicates` now has
four subcommands:

- `report` — scans the `Archive` table, writes a JSON report of every title
  shared by 2+ records, plus a Markdown file listing every collection that
  has at least one of those records. Also resolves each record's parent collection id to
  the collection's human-readable identifier, via a new `collection_table_name`
  scan.
- `apply` — disambiguates one collection's duplicate titles at a time,
  matched by the collection's `collection_identifier` (not its raw id).
- `rollback` — restores titles recorded in a `report` or `apply`
  change-log, scoped to one collection at a time, same as `apply`.
- `revert-legacy` — restores titles for a collection that was disambiguated
  by the *pre-`apply`* version of this tool, where no report or change-log
  exists to roll back from. Used this session to undo a real `vtec`
  collection run (see "What changed in this continuation session" below).

Full design rationale for the original apply/rollback build lives in
`spec.md` in this same directory (produced via `/mattpocock-skills:grill-me`
+ `/mattpocock-skills:to-spec`). It has not been published to an issue
tracker — no `mattpocock-skills` tracker/triage-label config exists for this
project yet; run `/setup-matt-pocock-skills` if that's wanted later. The
`README.md` in the tool's own directory is the up-to-date reference for
usage; this file is a narrower "what changed / what's next" note.

## Commands

```sh
# 1. Scan and write output/duplicate_titles_<timestamp>.json, plus
#    output/duplicate_titles_<timestamp>.md listing affected collections
archive-title-dedup report -config config.yaml

# 2. Preview one collection's renames (no writes)
archive-title-dedup apply -config config.yaml \
  -input output/<timestamp>_duplicate_titles.json \
  -collection_identifier FCHS_OBJ -suffix Map -dry-run

# 3. Apply for real -- writes title in DynamoDB and a change-log
archive-title-dedup apply -config config.yaml \
  -input output/<timestamp>_duplicate_titles.json \
  -collection_identifier FCHS_OBJ -suffix Map
# -> output/changelog_FCHS_OBJ_<timestamp>.json

# 4. Undo, scoped to the same collection, from either the change-log or the
#    original report
archive-title-dedup rollback -config config.yaml \
  -collection_identifier FCHS_OBJ \
  output/changelog_FCHS_OBJ_<timestamp>.json

# 5. Undo a pre-apply-era run with no report/change-log: re-derives originals
#    straight from the live table by stripping "<suffix>-<index>" off titles
#    that still have it
archive-title-dedup revert-legacy -config config.yaml \
  -collection_identifier vtec -suffix ": Specimen" -dry-run
archive-title-dedup revert-legacy -config config.yaml \
  -collection_identifier vtec -suffix ": Specimen"
```

`-collection_identifier` / `-suffix` fall back to `config.yaml` fields of the
same name if the flags are omitted, on both `apply` and `rollback`.

## Config (`config.yaml`)

```yaml
region: us-east-1
table_name: Archive-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev
collection_table_name: Collection-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev  # required for `report`
output_dir: output
output_file: duplicate_titles.json  # report writes <output_dir>/duplicate_titles_<timestamp>.json (+ .md)
concurrency: 10
# optional fallbacks for apply/rollback's -collection_identifier and apply's -suffix:
# collection_identifier: FCHS_OBJ
# suffix: Map
```

## Output / change-log shape (same schema for both)

```json
{
  "collection_identifier": "FCHS_OBJ",       // only set in a change-log
  "timestamp": "20260922T153000Z",           // only set in a change-log
  "duplicates": [
    {
      "title": "1957 Coeburn Quadrangle Virginia",
      "records": [
        {
          "id": "2bcd8e4f-...",              // DynamoDB primary key
          "identifier": "nmcst005196",
          "collection_id": "11783a71-...",   // parent collection's DynamoDB id
          "collection_identifier": "FCHS_OBJ", // parent collection's human-readable identifier
          "new_title": "1957 Coeburn Quadrangle Virginia - Map: nmcst005196" // only in a change-log
        }
      ]
    }
  ]
}
```

`collection_id`/`collection_identifier` are `null` on a record with no
parent collection, or if the collection id wasn't found in the collection
table at scan time.

## What changed in this continuation session

Picked up after the original `report`/`apply`/`rollback` build (see
`summary.md`'s first section) to fix two follow-up gaps the user flagged:

1. **Records now carry the collection's identifier, not just its id.**
   `parent_collection` was renamed to `collection_id` (still the raw
   DynamoDB collection key), and a new `collection_identifier` field was
   added, resolved from a new `collection_table_name` config setting that
   `report` scans once up front (`buildCollectionIndex`). `apply`'s
   `-collection_identifier` flag now matches against this resolved
   identifier instead of the raw collection id — this fixes a pre-existing
   naming mismatch (the flag was always called `collection_identifier` but
   used to compare against the raw id) and was confirmed with the user
   before making the behavior change.
2. **`rollback` is now scoped to one collection, like `apply`.** It
   previously reverted every record in the given file unconditionally.
   It now takes the same `-collection_identifier` flag (with the same
   `config.yaml` fallback) and only reverts matching records.
3. **Disambiguated title format now has a space after the colon.** The
   suffix format is `<original title> - <suffix>: <record identifier>`
   (was `<suffix>:<identifier>`, no space). User made this edit directly in
   `main.go`; tests and README were updated to match.
4. **`report`'s output filename is now timestamped.** It writes
   `<output_dir>/<timestamp>_<output_file>` (UTC `YYYYMMDDTHHMMSSZ`, same
   format as the change-log timestamp) instead of always overwriting
   `<output_dir>/<output_file>`, so successive `report` runs don't clobber
   each other.

`README.md` in the tool's directory and `main_test.go` were updated to
match; `go build`/`go vet`/`go test ./...` all pass.

## What changed in this second continuation session

The user had already run `apply` against the `vtec` collection with
`-suffix Specimen` using an *older* build of this tool (predating this
repo's `apply`/`rollback` commands — see git log for the pre-rewrite
commits, e.g. `4817ce1`), and no longer had the input report/change-log
needed for `rollback`. That old algorithm wrote
`<original title><suffix>-<zero-padded index>` directly with no audit
trail, unlike the current `apply`, which always writes a change-log.

Added `revert-legacy` (`main.go`): scans the live `Archive` table for
records in the given collection, matches titles against
`^(.*)<suffix>-\d+$`, and restores the captured original. No input file
needed — it works entirely from the live table's current state. Verified
via `-dry-run` first (2,239 matches, all correctly formed), then ran for
real: **2,239/2,239 `vtec` records reverted**, confirmed clean with a
follow-up `-dry-run` (zero remaining matches). Added
`TestPlanRevertLegacy_StripsSuffixAndIndex` to `main_test.go` and a
`revert-legacy` section to `README.md`.

This is a one-way trip in the sense that there's no change-log of *this*
revert — if `vtec` needs to be re-disambiguated, use the current `apply`
command, which will produce one.

## What changed in this third continuation session

1. **Timestamp moved to the end of the report filename.** `report` now
   writes `<output_dir>/<output_file stem>_<timestamp><ext>` (e.g.
   `output/duplicate_titles_20260922T153000Z.json`) instead of
   `<timestamp>_<output_file>`, so report files sort together by name.
   Commit `a0ef2b9`.
2. **`report` also writes a Markdown collection list.** Same path as the
   JSON but with a `.md` extension. It has a `# Collections with duplicate
   titles` heading and one bullet per collection identifier, sorted. A
   collection is listed if any of its records is in any duplicate-title
   group, even a group that spans several collections. That is exactly the
   set of collections `apply -collection_identifier` would change. Records
   with no resolved collection are left out. The file says "None." if
   there are no duplicates. Code: `duplicateCollections` and
   `collectionsMarkdown` in `main.go`. Commit `cf5e99f`.
3. README updated throughout for both changes (commits `cf5e99f`,
   `e65aa70`).

Only `go build`/`go vet` were run for these changes. `report` has not been
run against the live table since, so the `.md` output hasn't been seen on
real data. No unit tests were added for `duplicateCollections`.

## Important: regenerate `output/duplicate_titles_<timestamp>.json` before using `apply`/`rollback`

Any report file from before this session's `collection_identifier` change
has no `collection_identifier` field, so nothing in it will match `apply`
or `rollback`'s `-collection_identifier` flag. Run `report` again first
(this also requires `collection_table_name` to be set in `config.yaml`,
which it wasn't before this session).

## Next steps for whoever picks this up

1. Set `collection_table_name` in `config.yaml` if not already done, and
   re-run `report` to get a fresh `duplicate_titles_<timestamp>.json` with
   `collection_id`/`collection_identifier` populated. Use the matching
   `.md` file as the checklist of collections still to process.
2. `vtec` is now back to its original, pre-dedup titles (see the
   revert-legacy section above). If it still needs disambiguating, do it via
   the current `apply` command so a change-log gets written this time.
3. Pick another collection from the `.md` list, decide
   its `suffix` label, and run `apply -dry-run` against it to sanity-check
   output before a real run.
4. Nothing has been pushed to remote per standing instructions — push /
   open a PR on request.
5. `main_test.go` covers `planApply`/`planRollback`/`planRevertLegacy` (the
   pure seams) directly; the DynamoDB read/write paths (`scanSegment`,
   `writeJobs`, `buildCollectionIndex`, `scanCollectionTitles`,
   `collectionIDForIdentifier`) are exercised via dry-run/manual runs against
   the dev table, not unit-tested — this matches the testing approach agreed
   in `spec.md`.
