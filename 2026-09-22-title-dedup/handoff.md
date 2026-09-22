# Hand-off: archive-title-dedup

## Where things stand

`vtdlp-aws-tools/go/archive-title-dedup` on branch `fix-duplicates` now
contains a working (but not live-tested) Go CLI that scans an `Archive`
DynamoDB table for duplicate titles and writes a JSON report.

Run it with:

```sh
archive-title-dedup -report -config config.yaml
```

(`-report` is required — running without it just prints a usage message
and exits 1.)

## Config (`config.yaml`)

```yaml
region: us-east-1
table_name: Archive-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev
output_dir: output
output_file: duplicate_titles.json
concurrency: 10
```

## Output shape

```json
{
  "duplicates": [
    {
      "title": "Foo",
      "records": [
        {"identifier": "abc123", "parent_collection": "coll-1"},
        {"identifier": "def456", "parent_collection": null}
      ]
    }
  ]
}
```

Groups sorted by title, records within a group sorted by identifier.

## Next steps for whoever picks this up

1. **Run it for real** against a dev table and sanity-check the output —
   this has not been done yet. Watch for:
   - Whether `identifier` / `parent_collection` live at the top level of
     the DynamoDB item or nested (e.g. under an `Archive` attribute) — the
     code currently assumes top-level, matching the prior tool.
   - Whether `parent_collection` is stored as a DynamoDB List (`L`) of
     strings or a String Set (`SS`) — both are handled, but only those two.
2. Decide if `-report` is the right long-term flag name/behavior, or if it
   should default to on with a `-dry-run`-style opt-out instead — it was
   added as a literal "gate the existing process" request without further
   spec.
3. Push `fix-duplicates` to remote and open a PR when ready (not pushed
   yet, per standing instructions).
4. Consider adding a test file (`main_test.go` was deleted from the old
   version and not replaced) — none exists for this rewrite.
