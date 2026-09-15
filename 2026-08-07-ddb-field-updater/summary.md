# Session: Go tool to bulk-update a DynamoDB field by prefix match

**Date:** 2026-08-07
**Directory:** `/Users/whunter/dev/dlp/ingest/vtdlp-aws-tools/go/ddb-field-updater`
**Goal:** Build a Go application that scans a DynamoDB table, finds items where a configured field's value starts with a given prefix, rewrites that prefix, and writes the item back — with settings driven by a YAML config file.

## Design decisions (clarified with user up front)

1. **Replace mode:** only the matching leading prefix is swapped for the new value; the remainder of the original string is preserved and appended (not a full-value overwrite).
2. **Dry-run support:** added as a safety default for a bulk-mutating tool against a live table — `dry_run: true` in the config, and a `-dry-run` CLI flag that can force it on regardless of the config value.

## What was built

New Go module at `go/ddb-field-updater/` (module `vtdlp-aws-tools/ddb-field-updater`, Go 1.24):

- **`main.go`** — the tool:
  - Loads config from a YAML file (`-config`, default `config.yaml`); validates required fields (`region`, `table_name`, `field_name`, `match_prefix`) are present.
  - Uses AWS SDK for Go v2 (`aws-sdk-go-v2/config`, `.../service/dynamodb`), picking up credentials via the default provider chain (env vars, shared config/profile, SSO, instance/task role).
  - Calls `DescribeTable` once to get the table's key schema, purely so log lines can identify items by their real key attributes.
  - Paginates a full `Scan` of the table (`dynamodb.NewScanPaginator`).
  - For each item, checks the configured field exists and is a String (`S`) attribute type, and does a `strings.HasPrefix` check against `match_prefix`.
  - On match: computes `new_value + strings.TrimPrefix(old, match_prefix)`, and either logs it as a dry-run preview or updates the field in the item map and writes the whole item back via `PutItem` (preserving all other attributes untouched).
  - Prints a per-item log line and a final summary (`scanned`/`matched`/`updated`/`failed` counts); exits non-zero if any individual `PutItem` failed.
- **`config.yaml`** — example/template config with inline comments for `region`, `table_name`, `field_name`, `match_prefix`, `new_value`, `dry_run`.
- **`go.mod` / `go.sum`** — dependencies: `github.com/aws/aws-sdk-go-v2`, `.../config`, `.../service/dynamodb`, `gopkg.in/yaml.v3`.

Verified `go build` and `go vet` both pass; ran `go mod tidy` to finalize dependency versions.

## How to run (given to user)

```bash
cd go/ddb-field-updater
cp config.yaml myconfig.yaml   # edit region/table_name/field_name/match_prefix/new_value
go run . -config myconfig.yaml          # dry_run: true in config previews matches only
# flip dry_run to false in myconfig.yaml, or omit -dry-run, to actually write
go build -o ddb-field-updater .
AWS_PROFILE=your-profile ./ddb-field-updater -config myconfig.yaml
```

Required IAM permissions on the target table: `dynamodb:Scan`, `dynamodb:DescribeTable`, `dynamodb:PutItem`.

## Notes / caveats surfaced to user

- `Scan` reads the entire table (RCU cost, and time on large tables) — acceptable for a one-off migration but worth flagging for very large or high-traffic tables.
- This is the first Go tool added to the previously-empty `go/` directory in `vtdlp-aws-tools`, which otherwise contains Python-based ingest tooling (`batch_task_json_generator`, `format_obj_s3_upload`, etc.).

## State at end of session

- New files committed to disk (not yet git-committed): `go/ddb-field-updater/main.go`, `config.yaml`, `go.mod`, `go.sum`.
- No git commit was made — user has other unrelated uncommitted changes across the `vtdlp-aws-tools` repo (see `git status` at session start) and did not ask for a commit.
