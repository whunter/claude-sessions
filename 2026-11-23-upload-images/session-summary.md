# Session summary: upload-images (VTEC thumbnail uploader)

**Dates:** 2026-11-22 to 2026-11-23
**Repo:** `~/dev/dlp/ingest/vtdlp-aws-tools`, at `go/upload-images/`
**Branch:** `technical-metadata`. Commit `6311a7f`, not pushed.

## Goal

Upload the 106 VTEC thumbnails in `~/dev/dlp/assets/vtec/media/thumbs/` to
two S3 buckets, with templated keys. The tool is written in Go, uploads with
goroutines, and reads a YAML config so it can be reused.

## Design (settled through a grilling session)

### Targets and keys

- The config has a list of `targets`. Each target is a `bucket` plus a
  `key_template`, and every file is uploaded once to each target.
  - `ingest-dev-vtlib-store` → `federated/{collection}/{identifier}/3D/GLB/{filename}`
  - `ingest-dev.img.cloud.lib.vt.edu` → `federated/{collection}/{identifier}/3d/{filename}`
- Template placeholders: `{collection}`, `{identifier}` (the first capture
  group of `identifier_pattern`), `{basename}`, `{filename}` and `{ext}`.

### Uploads

- **No re-encoding.** The user's first example showed a `.jpg` key, but they
  decided to upload the PNG to both targets as-is.
- **Other extensions are left alone.** An existing object with the same name
  but a different extension (e.g. `…_thumbnail.jpg`) is not touched, and the
  PNG is written next to it. The tool doesn't look for or log these.
- **Which files.** Only the top level of the directory is read. A file is
  uploaded if it is a `.png` and its name matches `^(.+)_thumbnail$`. Other
  files are reported as `skip-no-match`, and dotfiles and directories are
  ignored.

### Existing objects

The tool matches existing objects against the full key, ignoring case.
- **Same key, same bytes:** skip and log it.
- **Same key, different bytes:** copy the existing object to
  `<name>_backup<ext>`, then overwrite it.
- **Key that differs only in case:** rename it to its own `_backup` (copy,
  then delete) and upload at the template's key.
- **A `_backup` already exists:**
  - If it holds different bytes, fail that file.
  - If it holds the same bytes, reuse it. A run interrupted between the
    backup and the upload leaves exactly this state, so re-runs are safe.
    The user didn't ask for this rule; I added it.

### Running, reporting and implementation

- **Dry run.** `-dry-run` does all the reads and no writes.
- **Report.** A CSV is written to `output/`. Each (file, target) pair succeeds
  or fails on its own, with no rollback. The tool exits 1 if anything failed.
- **Implementation details:**
  - Uploads use `feature/s3/transfermanager` (the old `manager` package is
    deprecated) with a SHA-256 checksum and Content-Type from the extension.
  - Buckets with dots in their names are addressed path-style.
  - Bytes are compared by MD5 from the ETag. If the ETag is from a multipart
    upload, the tool downloads the object and hashes it.

## Facts checked

- **Buckets:** both are in us-east-1.
  - `ingest-dev-vtlib-store` has versioning enabled.
  - `ingest-dev.img.cloud.lib.vt.edu` never had versioning enabled. Both use
    SSE-S3 (AES256).
- **Local folder:** 106 `*_thumbnail.png` files (250×250), plus logs, YAML,
  markdown and 2 directories.

## Files

`config.go`, `upload.go` (per-pair logic), `run.go` (scan, worker pool,
report), `main.go`, `fakes3_test.go`, `upload_test.go`, `config.yaml`,
`README.md` and `.gitignore`.

## Verification

- **Tests:** `go test -race ./...` passes. It covers upload, skip-identical,
  skip-identical when the existing object has a multipart ETag,
  backup-and-replace, the case-variant rename, reusing a backup, failing when
  the backup differs, several case matches, dry run, upload failure, a
  4-part multipart upload, scan, a two-target run with its report, and
  config validation.
- **Read-only dry run against the real buckets:**
  - 106 `upload`, all to vtlib-store.
  - 84 `backup-and-replace` and 22 `skip-identical` on the img bucket.
  - 7 `skip-no-match` and 0 `fail`.
