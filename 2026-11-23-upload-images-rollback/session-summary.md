# Session summary: upload-images rollback

**Date:** 2026-11-23
**Repo:** `~/dev/dlp/ingest/vtdlp-aws-tools`, at `go/upload-images/`
**Branch:** `technical-metadata`. Commits below; not pushed.
**Spec:** `rollback-spec.md` in this directory. It includes the decisions
and "As built" notes added during the session.

## Goal

Undo one upload-images run, restoring:
- the preservation bucket,
- the access bucket,
- the DynamoDB records it touched.

Neither the preservation bucket's versioning nor the table's point-in-time
recovery can do this, so each run's report CSV becomes the undo log.
Following the spec, the work was delivered in two pieces with a check-in
between them, test-first against the existing fakes.

## Commits (vtdlp-aws-tools, `technical-metadata`)

| Commit | What |
|---|---|
| `41a7257` | Piece 1: streamed step-level report and the new columns; a failed row keeps its intended action |
| `8688bcc` | A backup copy that lands despite an error is recorded as this run's |
| `11bea2b` | Piece 2: the `-rollback` command |
| `f30d09b` | Review fixes: rollback goes by object state; planned lines; shared bucket, torn line and dry-run fixes |

Spec updates in claude-sessions: `20075ed` and `55c5aab`.

## Piece 1: the forward-run report

- **Step lines.** After each completed step (`backup`, `upload`,
  `delete-variant`, `ddb`), a full snapshot of the row is appended and
  flushed, with `steps_done` cumulative and `;`-separated.
- **Planned lines.** Another line is written just before a row's first S3
  write and just before its `UpdateItem`. This came from the piece 2
  review.
- **Final rewrite.** A run that finishes replaces the file (tmp file, then
  rename) with one sorted line per row. A run that stops with an error
  keeps its step lines.
- **New columns:** `replaced_key`, `replaced_md5`, `backup_created`,
  `uploaded_md5`, `steps_done`, `ddb_table`, `ddb_record_id`,
  `old_thumbnail_state`, `old_updated_at`, `new_updated_at`.
  - `replaced_md5`, `new_updated_at` and `ddb_record_id` go beyond the
    spec. Rollback's checks need them.
- **Failed rows.** A failure while checking the bucket gives `fail`. A
  failure during the writes keeps the intended action.
- **Backup copies.** If a copy returns an error, the tool checks whether
  the backup landed anyway with the right bytes. If it did, the backup is
  recorded as made by this run.

## Piece 2: `-rollback`

```
upload-images -config config.yaml -rollback output/upload_<ts>.csv [-dry-run] [-yes]
```

- **Reading the report.** The last line per `local_path` + `bucket` wins,
  and a torn last line is ignored. It refuses:
  - dry-run reports,
  - old-format reports,
  - reports whose bucket or table differs from the config,
  - configs where preservation and access are the same bucket.
- **Order.** Each file is undone record, then access, then preservation.
  If one fails, the file's later steps show `cancelled`.
- **S3.** Rollback goes by what the objects hold now, not by `steps_done`
  alone, so a write that landed but went unrecorded is still undone.
  - Each object must hold either what the run left or what was there
    before. Anything else is drift: the row fails and nothing is written.
  - A backup is deleted only if this run made it and the original is back
    in place.
  - `steps_done` only decides between `nothing` and
    `skip-already-reverted`.
- **DynamoDB.** The revert reads the record with `GetItem`:
  - **It holds this run's values:** revert, using an `UpdateItem`
    conditioned on those values. `thumbnail_path` is put back exactly
    (REMOVE, NULL or the old string). `updatedAt` is put back, or removed
    if `old_updated_at` is empty.
  - **It holds the old values:** `skip-already-reverted` if the `ddb` step
    was recorded, otherwise `nothing`.
  - **It holds anything else:** drift.
- **Running it.**
  - `-dry-run` only reads.
  - A live run makes a dry pass, prints the counts and asks for `y`
    (`-yes` skips this).
  - It writes `rollback_[dryrun_]<ts>.csv` and exits 1 if any row failed.

## Decisions made with the user

- **Report layout:** snapshot lines plus a final rewrite; the table goes in
  a `ddb_table` column.
- **Test seams:**
  - `target.process` with a step callback,
  - the `run()` pipeline,
  - the report writer,
  - reading the report,
  - per-file rollback,
  - a full round trip from a real report file.
- **Record with no `updatedAt`:** an empty `old_updated_at` means rollback
  removes it.
- **`UpdateItem` sent but returned an error:** rolled back under the same
  condition.
- **The file is hashed and uploaded in two separate reads:** left as is.
- **Record id:** added `ddb_record_id` rather than re-deriving the
  identifier.

## Reviews

Two-axis reviews (Standards and Spec) ran after each piece.
- **Piece 1:** the reviews found the missing `new_updated_at` and
  `replaced_md5`, and the `finish(nil)` loss of the undo log.
- **Piece 2:** the reviews found a path that could delete the only copy of
  an original, and writes that landed but couldn't be undone. They also
  found several smaller bugs. All are fixed (`f30d09b`).

Left as is:
- Deletes aren't conditional (documented in the README).
- A dry-run report is spotted by its file name only.
- Duplicated summary and printing code, and `old_thumbnail_state` as a
  plain string.

## Verification

- `go test -race ./...` passes. The fake DynamoDB now evaluates
  `SET`/`REMOVE` and conditions joined with `AND`, and supports `GetItem`
  and "write lands, then error".
- Mutation spot checks confirmed the rollback tests catch broken
  cancellation, dry-run writes and backup-deletion guards.
- **Not run against AWS.** No real forward run or rollback was made this
  session.
