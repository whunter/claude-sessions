# Session Summary: archive-title-dedup

**Date:** 2026-09-21 – 2026-09-22
**Repo:** `vtdlp-aws-tools/go/archive-title-dedup`
**Branch:** `fix-duplicates`

## What happened

This directory previously held a Go tool that appended a suffix to duplicate
`Archive` titles in DynamoDB, driven by a JSON report of duplicates as input.
At session start, that tool's `main.go`, `main_test.go`, `go.mod`, and
`go.sum` were already deleted from the working tree (uncommitted), leaving
only a stale `config.yaml`.

Per the new request, the tool was rewritten from scratch as a **duplicate
finder** rather than a title mutator:

- Scans the `Archive` DynamoDB table named in `config.yaml`.
- Groups records by exact `title` match.
- For every title that appears more than once, records the title plus each
  matching record's `identifier` and `parent_collection[0]` (as
  `parent_collection` in the output; `null` if absent/empty).
- Writes the result as indented JSON to `<output_dir>/<output_file>`
  (defaults: `output/duplicate_titles.json`).
- Scans the table in parallel using DynamoDB's segmented scan: one goroutine
  per segment, count set by `concurrency` in `config.yaml` (default 10).
- Requires the `-report` flag to actually run the scan (`archive-title-dedup
  -report -config config.yaml`); without it, it exits with a usage message.
  This flag was added on request as a deliberate trigger/guard rather than
  running on every invocation.

## Key files

- `main.go` — full implementation (config loading, segmented scan,
  duplicate grouping, JSON report writing).
- `config.yaml` — `region`, `table_name`, `output_dir`, `output_file`,
  `concurrency`.
- `go.mod` / `go.sum` — regenerated (same module name/deps as the prior
  tool: aws-sdk-go-v2, dynamodb, yaml.v3).

## Commits (not pushed)

- `f88fae1` — Rewrite as duplicate-title finder: parallel scan, JSON report
- `4cf5212` — Require -report flag to run the duplicate-titles scan

## Not yet done / caveats

- **Not run against real DynamoDB.** Only `go build`/`go vet` were verified;
  no live scan or output was checked against the actual table.
- `identifier` and `parent_collection` are read as top-level item
  attributes (matching the old tool's assumption), not nested under an
  `Archive` map — confirm this matches the table schema if results look
  wrong.
- Old title-suffixing tool (deleted from the working tree before this
  session) is still recoverable from git history prior to commit `f88fae1`.
- Nothing has been pushed to remote per instructions; push on request.
