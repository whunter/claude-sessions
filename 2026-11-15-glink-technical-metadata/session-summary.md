# Session Summary: glink Technical Metadata (2026-11-15)

## Requests
1. Compile technical metadata for the Gretchen Link (glink) collection from the scanning guide in `docs/` and two example TIFFs. Write it to `technical_meta/technical_metadata.csv` and pivot to one row per file.
2. Save sources and notes in a sidecar file (`technical_metadata_sources.csv`).
3. Can the original TIFF metadata be recovered from the scaled JPEG derivatives in `media/scaled`?
4. Build the full CSV for every glink file, using the derivatives only where they accurately describe the original and the S3 originals for everything else, without downloading full images.
5. Design a production replacement (grilling session), then turn the design into GitHub issues.

## Outcomes

### Derivative recoverability (request 3)
Mostly recoverable. A derivative can't supply:
- checksums and file size
- the original capture filename (Photoshop slice name)
- the original TIFF Software and DateTime tags
- the exact copy of the ICC profile
- XMP ModifyDate, DocumentID and DerivedFrom
- the IFD1 thumbnail

For Phase One files, the export also overwrote Software, ColorSpace and ColorMode.

### Full CSV (request 4)
- `~/dev/dlp/assets/glink/technical_meta/technical_metadata.csv`: 536 rows (139 items) with 63 columns. New columns: `sequence_number`, `md5_checksum`, `s3_crc64nvme_checksum`, `s3_uri` and `technical_notes`.
- `technical_metadata_sources.csv` gives the source of each column and describes the method.
- How the data was read:
  - S3 head-object, plus ranged reads of the first 64 KB and last 256 KB of each object.
  - No full downloads; about 2:50 for all 536 files.
  - Those ranges covered every tag in every file.
- MD5 values come from the ETag. All 536 uploads were single-part, so the ETag is the MD5; this was checked against local MD5s of the two example files.
- Field selection: each derivative field was compared with the S3 value per file and used only when the two were identical.
- The glink folder isn't a git repo, so nothing there was committed.

### Collection facts
- Phase One: 400 files, items glink001001–010.
  - Schneider 120 mm Macro lens (350 files). Sketchbook 4 (glink001004, 50 files) was shot with a Schneider LS 45 mm f/3.5, which isn't in the scanning guide.
  - 425 ppi, 16-bit, ISO 50, 1/3 s or 0.4 s, f/8 or f/9.
  - The camera clock appears to be set to UTC: capture times run from 00:18 to 04:00, which would be evening sessions in Eastern time.
- i2s: 136 files across 129 items; 400 ppi, 8-bit.
- Discrepancies with the descriptive CSV:
  - glink001003: the descriptive CSV gives 2025-12-03, but the files were shot 2025-11-13 local time.
  - glink002071: the descriptive CSV gives 2025-11-07, but the item was scanned 2025-11-12, so its color target (lgpT001) is uncertain.

### Production tool design (request 5)
The grilling session settled the design of **techmeta**, a Go tool in `vtdlp-aws-tools/go/technical-metadata/`:
- still images from originals only; derivatives play no part
- our own TIFF, EXIF, XMP, ICC and Photoshop-resource parser over a common random-read interface; on S3, ranged GETs with a block cache
- local files first, falling back to S3, with a warning when sizes differ
- MD5 from single-part ETags; objects with a `-N` (multipart) ETag are stream-hashed in memory
- goroutine worker pool, Batch-style sharding and a `merge` subcommand
- CSV (versioned 63-column schema) and JSONL output
- per-collection YAML config with scoped overrides and clock offsets
- optional descriptive-CSV join, with cross-checks reported as warnings
- Lambda and Batch entry points; no deployment work for now

### GitHub issues
[vtdlp-aws-tools #4–#14](https://github.com/vt-digital-libraries-platform/vtdlp-aws-tools/issues), labelled `ready-for-agent` and `enhancement` (the `ready-for-agent` label was created for this). They use GitHub's built-in blocked-by links.

## Artifacts
- `prototype/`: the Python scripts used in this session (S3 header fetcher, TIFF/JPEG metadata parser, CSV builder). They're the reference behavior for the Go tickets.
