# Session: Go tool to rewrite IIIF tile info.json files, discovery driven by DynamoDB

**Date:** 2026-08-27
**Directory:** `/Users/whunter/dev/dlp/ingest/vtdlp-aws-tools/go/iiif-infoFile-modifier`
**Goal:** Build a Go application that finds IIIF `info.json` tile-metadata files on S3, backs each one up in place, and rewrites it to a corrected format — with the list of files to touch driven by DynamoDB Collection/Archive records rather than a blind S3 scan.

## How the tool evolved (built in stages across the session)

1. **Initial scaffold**: download an S3 `info.json`, back it up in place (`backup_info.json`, server-side `CopyObject`), transform, write back — bucket/`collection_prefix` from a YAML config. Built with a placeholder transform first, per explicit instruction to get the scaffold right before defining the JSON format.
2. **Concrete transform**: derived from user-supplied `incorrect_info.json`/`corrected_info.json` fixtures. `@id`, `width`, `height`, `tiles[]` preserved (tiles reordered to `scaleFactors` then `width`); `sizes` dropped; `@context`/`protocol`/`profile` hardcoded (all files come from the same tiler). Validated with two tests: exact match against the corrected fixture, and idempotency (re-running on already-corrected input is a no-op).
3. **S3 path scoping**: narrowed from "any key with a `tiles` segment" to exactly `<collection_prefix>/<tiles_dir_name>/<item>-<index>/info.json`, so IIIF `info.json` files elsewhere in the collection (differently formatted, per spec) are never touched.
4. **README.md** written covering all of the above.
5. **DynamoDB-driven discovery refactor** (done via `/goal` plan-mode workflow): replaced the S3 prefix scan entirely. See below.
6. **Archive-field bug fix**: the Archive table's link to its parent collection turned out to be its `collection` attribute, not `parent_collection` as originally assumed — found via a user bug report ("can't find Archive records for the queried Collection") after the first live-adjacent review. `findArchiveIdentifiers`'s scan filter was corrected accordingly (with an `ExpressionAttributeNames` placeholder, since `collection` is a DynamoDB reserved word).
7. **Rollback mode (`-rollback`)**: reverses the transform for each discovered `info.json` — reconstructs the pre-transform shape, recovers the `sizes` array (otherwise unrecoverable) from that key's `backup_info.json`, writes it back, then deletes the backup. Field values for the hardcoded original shape (including `sizeByWhListed` in `supports`) were confirmed against a real `backup_info.json` the user provided.
8. **Data-loss fix (skip-already-transformed)**: user reported that running the tool twice over the same collection caused the second run's backup step to overwrite the real original `backup_info.json` with already-corrected content, permanently losing `sizes`. Fixed by adding `isAlreadyTransformed` (detects the tool's own output via the `formats`/`qualities` keys only it ever adds to `profile`) and restructuring the main loop into skip → backup-only-pending → transform-only-pending phases, so an already-corrected file is left untouched (no backup, no rewrite) on subsequent runs.

## Final discovery design

Old approach: list every S3 object under `<collection_prefix>/<tiles_dir_name>/` and pattern-match on key shape — no actual knowledge of which items belong to the collection.

New approach:
1. **`findCollectionID`** — scans `collection_table` (DynamoDB) via `dynamodb.NewScanPaginator` with `FilterExpression: "identifier = :identifier"` for the record matching `collection_identifier` (config), returns its `id` attribute. Errors on zero or >1 matches, or a missing/non-string `id`.
2. **`findArchiveIdentifiers`** — scans `archive_table` with `FilterExpression: "parent_collection = :parent_collection"` matching that `id`, collects each matching record's `identifier` attribute (deduplicated). Non-fatal: a record missing `identifier` is logged as a warning and skipped, not a hard failure.
3. **`findInfoObjects`** (reworked) — for each archive identifier, lists S3 objects under `<tilesPrefix><identifier>-` and keeps the ones exactly one directory level deep named `info.json` — same matching logic as before, just scoped per-identifier instead of unscoped across the whole tiles directory. An identifier with zero S3 subdirectories (tiles not yet generated) simply contributes nothing.

(Note: `findArchiveIdentifiers`'s filter was later corrected to match on `Archive.collection`, not `parent_collection` — see below.)

Both DynamoDB helpers use raw `types.AttributeValue` maps (no `expression` builder package), matching the convention already established in the sibling `ddb-field-updater` tool (also schema-agnostic Scan+FilterExpression, same `dynamodb.NewScanPaginator` pagination pattern). Everything downstream (backup/download/transform/upload loop, dry-run, exit codes) is unchanged.

**Path semantics change** (explicit user correction mid-plan-review): `collection_identifier` is not just a DynamoDB lookup key — it's also the final path segment of the S3 collection root, appended after `collection_prefix`. So `collection_prefix + "/" + collection_identifier + "/"` replaces what used to be the whole of `collection_prefix`. Concretely, the old `collection_prefix: federated/glink` became `collection_prefix: federated` + `collection_identifier: glink` for equivalent output.

## Config additions

Three new required YAML fields: `collection_table`, `archive_table`, `collection_identifier`. `config.yaml`'s live values were updated (`collection_prefix: federated` + `collection_identifier: glink`); `collection_table`/`archive_table` were left as placeholders since the actual DynamoDB table names weren't known this session. (`config.yaml` is gitignored — not committed.)

## Rollback design (superseded — see "Rollback refactor" below)

Originally, `rollbackInfoJSON(currentData, backupData []byte) ([]byte, error)` reversed `transformInfoJSON`: it took the corrected `info.json` (for `@id`/`width`/`height`/`tiles`) plus the paired `backup_info.json` (for `sizes`, which the forward transform drops and can't otherwise be reconstructed), and re-emitted the pre-transform shape — hardcoded `@context`/`protocol`/`profile` with `supports: ["cors", "sizeByWhListed", "baseUriRedirect"]`, matching `incorrect_info.json`. `runRollback` did this per discovered key, then deleted that key's `backup_info.json`; a missing backup failed that one key (counted in the `failed` summary total) without deleting anything. This was verified via `TestRollbackInfoJSON_ReversesTransform`, which transformed `incorrect_info.json` then rolled it back using the same file as its own "backup" and checked the round trip reproduced it exactly.

This approach was replaced in a follow-on session (2026-08-28) — see "Rollback refactor" below.

## Skip-already-transformed design (data-loss fix)

`isAlreadyTransformed(data []byte) (bool, error)` inspects `profile[1]` for a `formats` key — a shape only this tool's own output ever has (via the hardcoded `requiredProfile`/`profileExtra`). `runTransform` was restructured into three phases: (1) download every discovered key and classify each as skip/pending via `isAlreadyTransformed`, incrementing a new `skipped` counter for already-corrected files; (2) back up only the pending (still-original) files — if any backup fails, abort before modifying anything, as before; (3) transform and upload only the pending files. This prevents a second run over the same collection from backing up an already-corrected file over the true original and losing data like `sizes` — which is exactly what happened to the user before this fix (confirmed by inspecting the `backup_info.json` they provided, which matched the *output* format instead of the input format). Verified via `TestIsAlreadyTransformed`.

## Verification

`gofmt -l .` (clean), `go vet ./...` (clean), `go build ./...` (clean), `go mod tidy` (promoted `aws-sdk-go-v2/service/dynamodb` from indirect to direct dependency), `go test ./...` (all four tests pass: transform-matches-fixture, idempotency, rollback-reverses-transform, isAlreadyTransformed). No live AWS/DynamoDB access available in this environment at any point in the session, so no end-to-end run against real tables — all verification is fixture-based unit testing.

## Rollback refactor (2026-08-28 follow-on session)

While spot-testing keys directly against the real dev bucket (`s3://ingest-dev.img.cloud.lib.vt.edu/federated/glink/tiles/...`, via manual `aws s3 cp ... -` reads — `glink001001-1`, `glink001001-2`, `glink002129-1` were all confirmed to be correctly processed: `info.json` in output format, `backup_info.json` in valid pre-transform format), the user asked whether rollback would be better implemented as a copy-based restore (like `aws s3 mv backup_info.json info.json`) rather than JSON reconstruction. Reasoning discussed and agreed: it's both faster (fewer round trips — no need to download/reconstruct/re-upload the current `info.json`, just validate the backup and server-side copy it) and more correct (restores the *actual* original bytes rather than an approximation reconstructed from hardcoded `supports` values, which could be wrong if any real original ever had different `supports`).

Implemented:
- Removed `rollbackInfoJSON` and its supporting types (`rollbackProfile`, `rollbackProfileExtra`, `rollbackSize`, `backupSizes`, `rollbackTile`, `rollbackInfo`).
- Added `isPreTransformShape(data []byte) (bool, error)` — the inverse check of `isAlreadyTransformed`: confirms a non-empty `sizes` array and no `formats` key in `profile[1]`.
- Renamed `backupObject` → `copyObject` (now used bidirectionally: original→backup during transform, backup→original during rollback).
- Rewrote `runRollback`: for each key, download `backup_info.json`, validate via `isPreTransformShape` (fail that key if invalid, without touching anything), then `copyObject(backupKey, infoKey)` and `deleteObject(backupKey)`.
- Updated `main_test.go` (`TestRollbackInfoJSON_ReversesTransform` → `TestIsPreTransformShape`) and `README.md`'s Rollback/Development/IAM sections.
- Verified clean: `gofmt`, `go vet`, `go build`, `go test ./...` (all pass).
- Committed as `a1c21e8` — "Rollback: restore backup_info.json in place instead of reconstructing it".

## Live verification and concurrency refactor (2026-08-28 follow-on session, continued)

After the rollback refactor above, the user ran the tool live against the real collection twice: `-rollback`, then a normal forward-transform run. Both were spot-checked against three sample keys (`glink001001-1`, `glink001001-2`, `glink002129-1`) via manual `aws s3 cp ... -` reads before and after each run, and both matched expectations exactly — pre-transform shape with `backup_info.json` deleted after rollback; correctly re-transformed `info.json` with a valid `backup_info.json` restored after the forward run. This was the tool's first confirmed live run against real AWS infrastructure this project.

The user then asked whether the tool takes advantage of Go's concurrency model, since all S3/DynamoDB work was strictly sequential. Assessment: yes, meaningfully — per-key work (download/backup/transform/upload, or the rollback sequence) is independent across keys and pure I/O-bound network calls, so a bounded worker pool should cut wall-clock time roughly in proportion to concurrency for any collection with more than a handful of keys.

Implemented:
- Added `runConcurrent(n, concurrency int, fn func(i int))` — a generic bounded worker pool (semaphore channel + `sync.WaitGroup`) that calls `fn(i)` for each index, letting each call write its result into a pre-sized slice at its own index (no locking needed) so results can be logged afterward in original key order despite running out of order.
- Parallelized `findInfoObjects`'s per-archive-identifier S3 listing.
- Parallelized `runTransform`'s three phases: classify (download + `isAlreadyTransformed`), backup (`copyObject`), and transform+upload — each phase's network calls run concurrently, then results are aggregated/logged sequentially afterward.
- Parallelized `runRollback`'s per-key download/validate/restore/delete sequence.
- Added a `concurrency` config key (default 10) controlling the worker-pool size; DynamoDB collection/archive discovery (`findCollectionID`/`findArchiveIdentifiers`) was left sequential since Scan pagination is inherently ordered (each page depends on the last).
- Updated `config_example.yaml` and `README.md` (new Configuration row + a "Concurrency" subsection).
- Verified with `go test ./... -race` (race detector clean) in addition to the usual `gofmt`/`go vet`/`go build`.
- Committed as `f40381e` — "Run S3/DynamoDB requests concurrently instead of sequentially".

**Not yet live-tested**: this concurrency change had only been verified via build/vet/test (`-race` included, clean), not an actual run against DynamoDB/S3.

## Concurrency refactor confirmed live (same follow-on session, continued)

The user then ran the concurrency-enabled build live against the full `glink` collection (`config.yaml` already had real table names filled in: `Collection-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev`, `Archive-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev`):

- **Forward transform, live, `concurrency=10`**: discovered `collection id=07bc52cc-a44d-4488-b28d-e19d4e03cc22`, 139 archive identifiers, 536 `info.json` objects. Every one was already in corrected format from the prior (pre-concurrency) forward run, so all 536 were correctly skipped: `done: found=536 skipped=536 backed_up=0 modified=0 failed=0`. Spot-checked the 3 sample keys afterward — unchanged and correct, confirming the skip-safety logic holds under concurrent classification.
- **`-rollback`, live, `concurrency=10`**: run by the user against the same full collection. Spot-check of the 3 sample keys afterward confirmed all three correctly reverted to pre-transform shape (`sizes` present, `sizeByWhListed` in `supports`) with their `backup_info.json` deleted.

This confirms the concurrency refactor works correctly for both modes against the real 536-object collection, not just synthetically. Only the 3 sample keys were individually re-inspected after these full-collection runs — the rest were verified only via the aggregate summary-line counts.

**Not yet live-tested**: unlike the rollback refactor, this concurrency change has only been verified via build/vet/test (including `-race`), not an actual run against DynamoDB/S3 — the two live runs described above happened on the pre-concurrency build.

## Process note

The DynamoDB discovery refactor went through `/goal` + plan mode: two Explore/Plan subagents were used (one to research the sibling `ddb-field-updater` tool's DynamoDB conventions, one to design the concrete implementation) before writing code. The plan was revised once after `ExitPlanMode` based on user feedback (the `collection_prefix`/`collection_identifier` path-concatenation correction above) before implementation began. The `Archive.collection` field fix, rollback mode, and skip-already-transformed fix were each implemented directly (no plan mode) in response to specific user bug reports/feature requests.

## State at end of session

Working tree clean on branch `iiif-infoFile-modifier`. Five commits made (each requested explicitly by the user):

- `f40381e` — Run S3/DynamoDB requests concurrently instead of sequentially
- `a1c21e8` — Rollback: restore backup_info.json in place instead of reconstructing it
- `e3bdff3` — Add -rollback mode and skip already-transformed info.json files
- `fe93a8f` — Match Archive.collection instead of Archive.parent_collection
- `b59c2fe` — Drive iiif-infoFile-modifier discovery from DynamoDB instead of an S3 scan

The tool has been confirmed working live against the real dev bucket/DynamoDB tables for both modes, both pre- and post-concurrency-refactor (rollback + forward transform, each spot-checked correct) — see "Live verification and concurrency refactor" and "Concurrency refactor confirmed live" above. `config.yaml` (gitignored, local-only, not committed) has real values filled in (`Collection-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev` / `Archive-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev`), not the placeholders from earlier in this doc. See `handoff.md` for outstanding next steps.
