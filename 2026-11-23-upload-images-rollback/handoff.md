# Hand-off: upload-images rollback

This supersedes the state in `../2026-11-23-upload-images/handoff.md`. In
particular, versioning is the other way round from that file: as checked
for the spec, the preservation bucket `ingest-dev-vtlib-store` is **not**
versioned, and the access bucket is.

## State

- `go/upload-images/` on branch **`technical-metadata`** in
  `~/dev/dlp/ingest/vtdlp-aws-tools`. The latest commit is `f30d09b`.
  **Not pushed.** It probably belongs on its own branch before a PR.
- The forward report format changed (see `session-summary.md`).
  **Reports written before `41a7257` can't be rolled back.** Rollback
  refuses them as old-format.
- Everything is tested on fakes only. **Nothing has been run against AWS.**

## Next steps

1. **Try it on a scratch prefix first.** Point `collection` (or the key
   templates) at a throwaway prefix in the dev buckets, with a test record
   or two. Then:
   ```
   cd ~/dev/dlp/ingest/vtdlp-aws-tools/go/upload-images
   go build -o upload-images .
   ./upload-images -config scratch.yaml
   ./upload-images -config scratch.yaml -rollback output/upload_<ts>.csv -dry-run
   ./upload-images -config scratch.yaml -rollback output/upload_<ts>.csv
   ./upload-images -config scratch.yaml -rollback output/upload_<ts>.csv -dry-run   # expect all skip-already-reverted
   ```
   Things to check on real S3:
   - `HeadObject` NotFound handling.
   - `CopySourceIfMatch` and `IfNoneMatch` on `CopyObject` for the dotted,
     path-style access bucket.
   - The DynamoDB `REMOVE`/`SET` revert.
2. **Check the prompt by hand.** The decline path is tested. Also try `y`
   and `-yes`.
3. **Optional tidy-ups the review left open:**
   - shared summary and printing code for the two commands,
   - a typed `old_thumbnail_state`,
   - conditional deletes, if general-purpose buckets support `If-Match` on
     `DeleteObject`.

## Limitations (in the README)

- **No CloudFront invalidation.** An access image restored at the same key
  may be served from cache until it expires.
- **Deletes aren't conditional.** A change made in the moment between the
  check and the delete isn't caught.
- **Several runs:** roll back newest first. Drift checks refuse anything a
  later run changed.

## Unrelated untracked files in vtdlp-aws-tools

`go/ddb-field-updater/`, `go/iiif-infoFile-modifier/`, `go/x3d-batch-rotate/`
and two scripts in `batch_task_json_generator/`. They were there before
this session and were left alone.
