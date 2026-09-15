# Hand-off: Go tool to bulk-update a DynamoDB field by prefix match

**Directory:** `/Users/whunter/dev/dlp/ingest/vtdlp-aws-tools/go/ddb-field-updater`

## Current state

- New Go module built and verified (`go build`, `go vet`, `go mod tidy` all pass): `main.go`, `config.yaml`, `go.mod`, `go.sum`.
- Files exist on disk but are not git-committed. The parent `vtdlp-aws-tools` repo had other unrelated uncommitted changes at session start.
- Tool scans a DynamoDB table, replaces a configured field's matching prefix (preserving the remainder of the string), and writes items back, with a `dry_run` config option and `-dry-run` CLI override.
- This is the first Go tool in the repo's previously Python-only `go/` directory.

## Not yet done

- No git commit made — needs to be scoped separately from the other unrelated uncommitted changes in the repo.
- Never run against a real/live DynamoDB table — only `go build`/`go vet` verified, no functional test run (dry-run or otherwise) against actual data.

## Next steps

1. Review `git status` in `vtdlp-aws-tools` and stage only the `go/ddb-field-updater/` files for commit, leaving unrelated changes untouched.
2. Copy `config.yaml` to a real target config (`region`, `table_name`, `field_name`, `match_prefix`, `new_value`) and run with `dry_run: true` first to preview matches on the actual table.
3. Confirm the IAM identity used has `dynamodb:Scan`, `dynamodb:DescribeTable`, `dynamodb:PutItem` on the target table.
4. Once dry-run output looks correct, flip `dry_run: false` (or drop `-dry-run`) to perform the live update, and spot-check a few updated items afterward.
