# Hand-off: archive-title-dedup

## Where things stand

`vtdlp-aws-tools/go/archive-title-dedup` on branch `fix-duplicates` now has
three subcommands:

- `report` — scans the `Archive` table, writes a JSON report of every title
  shared by 2+ records (unchanged from earlier today, except the scan now
  also projects each record's DynamoDB primary key, `id` — see below).
- `apply` — disambiguates one collection's duplicate titles at a time.
- `rollback` — restores titles recorded in a `report` or `apply` change-log.

Full design rationale lives in `spec.md` in this same directory (produced via
`/mattpocock-skills:grill-me` + `/mattpocock-skills:to-spec` this session).
It has not been published to an issue tracker — no
`mattpocock-skills` tracker/triage-label config exists for this project yet;
run `/setup-matt-pocock-skills` if that's wanted later.

## Commands

```sh
# 1. Scan and write output/duplicate_titles.json
archive-title-dedup report -config config.yaml

# 2. Preview one collection's renames (no writes)
archive-title-dedup apply -config config.yaml \
  -input output/duplicate_titles.json \
  -collection_identifier <uuid> -suffix Map -dry-run

# 3. Apply for real -- writes title in DynamoDB and a change-log
archive-title-dedup apply -config config.yaml \
  -input output/duplicate_titles.json \
  -collection_identifier <uuid> -suffix Map
# -> output/changelog_<uuid>_<timestamp>.json

# 4. Undo, from either the change-log or the original report
archive-title-dedup rollback -config config.yaml output/changelog_<uuid>_<timestamp>.json
```

`-collection_identifier` / `-suffix` fall back to `config.yaml` fields of the
same name if the flags are omitted.

## Config (`config.yaml`)

```yaml
region: us-east-1
table_name: Archive-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev
output_dir: output
output_file: duplicate_titles.json
concurrency: 10
# optional fallbacks for apply's flags:
# collection_identifier: <uuid>
# suffix: Map
```

## Output / change-log shape (same schema for both)

```json
{
  "collection_identifier": "11783a71-...",   // only set in a change-log
  "timestamp": "20260922T153000Z",           // only set in a change-log
  "duplicates": [
    {
      "title": "1957 Coeburn Quadrangle Virginia",
      "records": [
        {
          "id": "2bcd8e4f-...",              // DynamoDB primary key
          "identifier": "nmcst005196",
          "parent_collection": "11783a71-...",
          "new_title": "1957 Coeburn Quadrangle Virginia - Map:nmcst005196" // only in a change-log
        }
      ]
    }
  ]
}
```

## Important: regenerate `output/duplicate_titles.json` before using `apply`

The table's actual DynamoDB partition key is `id` (a separate UUID from the
business `identifier` field) — confirmed via `aws dynamodb describe-table`.
The scan wasn't projecting it until this session, so **any existing
`output/duplicate_titles.json` from before this change has empty `id`
fields** and cannot be used for a real `apply`/`rollback` write (only for
`-dry-run`, which doesn't need the key). Run `report` again first.

## Next steps for whoever picks this up

1. Re-run `report` to get a fresh `duplicate_titles.json` with `id` populated.
2. Pick one collection from the 13 present (see `spec.md`'s Further Notes for
   the current group/collection breakdown), decide its `suffix` label, and
   run `apply -dry-run` against it to sanity-check output before a real run.
3. Nothing has been pushed to remote per standing instructions — push /
   open a PR on request.
4. `main_test.go` covers `planApply`/`planRollback` (the pure seam) directly;
   the DynamoDB read/write paths (`scanSegment`, `writeJobs`) are exercised
   via dry-run/manual runs against the dev table, not unit-tested — this
   matches the testing approach agreed in `spec.md`.
