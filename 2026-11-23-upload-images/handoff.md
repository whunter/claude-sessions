# Hand-off: upload-images

## State

- The tool is in `~/dev/dlp/ingest/vtdlp-aws-tools/go/upload-images/`. It's
  committed as `6311a7f` on branch **`technical-metadata`**, the branch that
  was checked out, and **not pushed**. It probably belongs on its own branch
  before a PR.
- **The real upload has not been run.** Only a dry run was done (report:
  `go/upload-images/output/upload_dryrun_20261122T140928.csv`, gitignored).
- `config.yaml` is set up for the VTEC thumbnail job.

## To run

```
cd ~/dev/dlp/ingest/vtdlp-aws-tools/go/upload-images
go build -o upload-images .
./upload-images -config config.yaml -dry-run   # re-check
./upload-images -config config.yaml
```

What to expect:
- **vtlib-store:** 106 new objects at `…/3D/GLB/VTEC…_thumbnail.png`.
- **img bucket:** 84 existing thumbnails copied to `…_thumbnail_backup.png`
  and then replaced, and 22 skipped because they're identical.
- **Re-running** is safe: identical objects are skipped and existing backups
  with the same bytes are reused.

## Open decision

**Case-insensitive matching covers the file name only.** S3 lists by a
case-sensitive prefix, so the folder part of the key must match exactly.
Matching the whole key would mean listing all of `federated/vtec/` for
every file. I recommended keeping it this way. The user hasn't confirmed,
and it's documented in the README under Limitations.

## Other limitations (in the README)

- **Some ETags aren't MD5s.** Objects encrypted with SSE-KMS or SSE-C have
  ETags that look like MD5s but aren't. The tool would then see identical
  objects as different. Both buckets use SSE-S3, so this doesn't apply.
- **No objects over 5 GiB.** Backups use a single `CopyObject`, which can't
  copy more than that.

## Unrelated untracked files in vtdlp-aws-tools

`go/ddb-field-updater/`, `go/iiif-infoFile-modifier/`, `go/x3d-batch-rotate/`
and two scripts in `batch_task_json_generator/`. They were already there
before this session. I left them alone.
