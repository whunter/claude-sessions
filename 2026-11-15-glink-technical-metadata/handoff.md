# Hand-off: glink Technical Metadata → techmeta

## State
- **glink CSV:** done. `~/dev/dlp/assets/glink/technical_meta/technical_metadata.csv` (536 rows) and `technical_metadata_sources.csv`. That folder isn't a git repo. The earlier 2-row example CSV was in the session scratchpad and is gone; it isn't needed.
- **techmeta (the Go tool):** designed and ticketed, no code yet. Issues are vtdlp-aws-tools #4–#14. Start with **#4**, the only issue nothing blocks; after it, #5, #6 and #7 can be worked on in parallel.

## Ticket dependency graph
```
#4 tracer bullet (local TIFF → CSV)
├─ #5 S3 source + checksums ─┬─ #8 input resolution + fallback ─┬─ #11 descriptive join
│                            └─ #9 JSONL + output destinations ──┤
├─ #6 EXIF fields ── #10 YAML config ────────────────────────────┘ (#11 also needs #10)
└─ #7 XMP/8BIM/ICC
#12 sharding + merge   ← #8, #9
#13 Lambda/Batch entry ← #12
#14 glink golden run   ← #7, #11, #12
```

## Before you start on techmeta
- Location: `~/dev/dlp/ingest/vtdlp-aws-tools/go/technical-metadata/`, module `technical-metadata`, binary `techmeta`.
- Conventions from the sibling tools (e.g. `flatten-collection`): Go 1.24.2, aws-sdk-go-v2, yaml.v3, `config.yaml`, fake-S3 tests.
- **Branch:** create a `technical-metadata` branch. `main` is one commit ahead of origin, and the repo has unrelated untracked work in `ddb-field-updater/`, `iiif-infoFile-modifier/`, `x3d-batch-rotate/` and `batch_task_json_generator/run-task-generator.sh`. Stage only `go/technical-metadata/`.
- **Deployment:** out of scope (no Dockerfile or IaC). The Lambda and Batch entry points are code only.
- **Fixtures:** the repo is public. Fixtures must be header-only, with the image data and embedded thumbnail replaced by dummy bytes. Serials and dates may stay.
- **Reference implementation:** `prototype/` in this folder.
  - `tiffmeta.py`: a parser over sparse head/tail buffers.
  - `extract.py`: field mapping.
  - `build_csv.py`: column assembly and date checks.

  The reference output is the glink CSV above.

## TIFF layout gotchas
- **Phase One (Capture One):** IFD0, every data blob and the IFD1 thumbnail sit in roughly the last 70 KB of the file.
- **i2s (Photoshop):** IFD0 is at offset 8, the blobs are in the first ~28 KB, and the ExifIFD is in the last ~1.2 KB.
- **ICC profiles:** both device types use Adobe RGB (1998), but the copies differ: 560 bytes / "Copyright 2000" for Phase One versus 544 bytes / "(c) 1998" for i2s.
- **Phase One clock:** it records UTC. Apply the offset only for cross-checks and date matching; don't rewrite stored values.

## Open items for the user
- Fix the capture_date for glink001003 in the descriptive CSV (it should be 2025-11-13).
- Confirm glink002071's scan date and color target.
- Decide whether the scanning guide should list the 45 mm lens.
