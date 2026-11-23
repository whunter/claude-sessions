# upload-images: rollback spec

Status: agreed design, not yet implemented. Tool lives at
`vtdlp-aws-tools/go/upload-images`.

## Goal

Undo one upload-images run: restore the preservation bucket, the access
bucket and the DynamoDB records it touched to their state before that run.

## Why the report is the undo log

Checked 2026-11-23:

| Resource | Rollback-relevant state |
|---|---|
| `ingest-dev-vtlib-store` (preservation) | versioning never enabled |
| `ingest-dev.img.cloud.lib.vt.edu` (access) | versioning enabled |
| `Archive-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev` | point-in-time recovery disabled |

S3 versions and DynamoDB restores can't cover all three, so each run's report
CSV is extended to record everything needed to reverse it.

## Part 1: forward-run report changes

### Streamed, step-level writes

The report is appended to and flushed as work happens: one line per completed
step (`backup`, `upload`, `delete-variant`, `ddb`). A crash or kill loses at
most the step that was running and not yet recorded. Rollback's drift checks
(below) catch that one.

### New columns

| Column | Meaning |
|---|---|
| `uploaded_md5` | MD5 of the bytes put at `key`; used for drift checks |
| `replaced_key` | the existing object that was backed up (the case variant for `rename-variant-and-upload`) |
| `backup_created` | `true` if this run made the backup, `false` if it reused one from an earlier run |
| `old_thumbnail_state` | `missing` / `null` / `string` |
| `old_updated_at` | the record's `updatedAt` before the update |
| `steps_done` | completed steps for the row, rebuilt from the step lines |

The DynamoDB table name is also recorded (header comment or column).

### Failed rows

A failed row keeps its intended `action` (e.g. `rename-variant-and-upload`)
instead of being overwritten with `fail`. `steps_done` shows how far it got,
and the error stays in `error`.

## Part 2: `-rollback`

```
upload-images -config config.yaml -rollback output/upload_<ts>.csv [-dry-run] [-yes]
```

Bucket and table names come from the config.

### It refuses some reports outright

- old-format reports (missing the new columns)
- dry-run reports
- reports whose row `bucket` values or table don't match the config

### Order and cancellation

Each file is undone in the reverse of forward order: **DynamoDB, then access,
then preservation**. If a step fails or finds drift, the file's later steps are
reported as `cancelled`, so a record never points at a missing object.

### S3, per row

Only the steps listed in `steps_done` are undone.

| Forward action | Rollback |
|---|---|
| `upload` | delete `key` |
| `backup-and-replace` | copy the backup back to `key`; delete the backup only if `backup_created` |
| `rename-variant-and-upload` | copy the backup to `replaced_key`, delete `key`, delete the backup only if `backup_created` |
| `skip-identical`, `skip-no-match`, `cancelled` | nothing |

**Drift check:** before touching `key`, confirm it still holds `uploaded_md5`
(ETag when it is a plain MD5, otherwise download and hash). If it doesn't,
the row fails and nothing is overwritten.

### DynamoDB

Only rows whose `ddb` step completed with `ddb_action=update`:

- `thumbnail_path` is restored exactly: REMOVE if `missing`, NULL if `null`,
  the old string if `string`.
- `updatedAt` is restored to `old_updated_at`.
- The `UpdateItem` only succeeds if the record still exists and holds both the
  `thumbnail_path` and the `updatedAt` this run wrote. Otherwise the row fails
  as drift.

Decided 2026-11-23, after piece 1:

- An empty `old_updated_at` means the record had no `updatedAt`; rollback
  REMOVEs it.
- Rows with `ddb_action=fail` and a non-empty `new_updated_at` (the
  `UpdateItem` was sent but returned an error, e.g. a timeout) are also
  rolled back, under the same condition. If the write never landed, the
  record won't hold this run's values, and the row is
  `skip-already-reverted` (it already holds the old values) or drift.
- Piece 1 also records `replaced_md5` and `new_updated_at`, which the
  re-run and drift checks use.

### Re-running

An interrupted rollback can be run again. Items already reverted are reported
as `skip-already-reverted` rather than as drift:

- an `upload` row whose key is already gone
- a replace whose key already holds the backup's bytes, with the backup gone
  (or kept because this run didn't create it)
- a record that already holds the old values

### Which runs, safety, output

- Any past report can be rolled back. If several runs need undoing, roll back
  newest first; the drift checks refuse items a later run changed.
- `-dry-run` makes only the read calls and reports planned actions.
- A live run prints the planned counts and asks for `y`; `-yes` skips the
  prompt.
- Writes `rollback_<ts>.csv` (`rollback_dryrun_<ts>.csv` for a dry run),
  prints counts and failing rows, and exits 1 if any row failed.
- Uses the same `concurrency` worker pool, one file per job.

## Out of scope

- **CloudFront invalidation.** Add to README limitations: an access image
  restored at the same key may be served from cache until it expires.

## Delivery

Build test-first against the existing fakes (`fakes3_test.go`,
`fakeddb_test.go`), in two pieces with a check-in between:

1. Forward-run report changes (streamed steps, new columns, intended action
   kept on failure, table recorded).
2. The `-rollback` command.
