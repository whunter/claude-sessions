# IAWA Media Copy — Session Summary

**Date:** 2026-09-10 to 2026-09-11
**Session name:** iawa-media-copy

## Task

For each of the 24 collection records in `/Users/whunter/dev/dlp/assets/iawa/meta/collection_exports`, look up `collection.identifier` in account `196766403141`, bucket `img.cloud.lib.vt.edu`, prefix `iawa`, and copy the matching subdirectory's files to the same path in account `226388486048`, bucket `vtdlp-s3-tunnel-dev`. Source files must not be modified — copy only, no move/delete/sync with `--delete`.

## Key findings

- Both source and destination buckets were reachable with the default AWS credentials in this environment (no profile switching needed) — the default identity already had cross-account access to both.
- One identifier mismatch: the CSV for `Ms1998_005` has `identifier = Ms1998_005`, but the actual S3 subdirectory is `Ms1998_005_Zimbler` (confirmed via the CSV's `title` field: "Liane Zimbler Architectural Collection..."). User approved treating this as a match and copying to `Ms1998_005_Zimbler` in both source and destination.
- The `iawa/` prefix in the source bucket contains other subdirectories not in the 24-collection list (`GottliebTiles`, `Ms1997_006_Rupp`, `Ms2000_051_HallJohnson`, `Ms2006_010_ONeill`, `WIL`) — these were correctly excluded.
- Total volume across the 24 target collections: ~8.37M objects, ~1.23 TiB (dominated by IIIF image tile pyramids — huge numbers of small files, not large blobs). Two collections alone account for over half the data: `Ms2013_090_Laleyan` (2.84M objects / 319 GB) and `Ms1990_057_Chadeayne` (144 GB).
- Running 6 `aws s3 cp --recursive` jobs in parallel against `vtdlp-s3-tunnel-dev` caused intermittent per-file `Read timeout` / `Could not connect` errors (destination endpoint apparently rate/connection-limited under concurrent load). These were individually low in count (11-13 per collection) and were fixed by retrying the specific failed files.
- One collection (`Ms1990_057_Chadeayne`) suffered a **fatal** listing error (`Connection was closed... continuation-token...`) that aborted its `aws s3 cp` job entirely, partway through (only ~6.6 GB of 144 GB copied at time of failure). This was NOT caught by the per-file failure count — it required comparing full source/destination object counts to detect. Recovered by re-running with `aws s3 sync` (idempotent, only copies missing/different objects) twice until the object counts matched exactly.
- A background-task execution quirk was hit twice: a `while read line; do ... aws s3 cp ...; done < file` loop pattern, when run via the harness's `run_in_background`, hung indefinitely with zero progress (no error, no crash, just silent). Switching to a flat script of explicit `aws s3 cp` command lines (no read-loop, no `timeout` wrapper) run in the foreground fixed it immediately. Worth remembering if scripting further batch retries in this environment.

## Outcome at session end

**10 of 24 collections copied and verified** (object count + total byte size match exactly between source and destination):

| Collection | Objects | Size |
|---|---|---|
| Ms1988_017_Pfeiffer | 43,188 | 10,238,657,903 |
| Ms1990_007_Leviseur | 572,017 | 51,922,411,792 |
| Ms1990_025_Rudoff | 49,803 | 6,489,481,928 |
| Ms1990_057_Chadeayne | 401,888 | 144,410,862,752 |
| Ms1991_025_Bliznakov | 12,539 | 1,350,815,750 |
| Ms1992_028_Rodeck | 516,627 | 129,384,087,937 |
| Ms1994_016_Crawford | 121,263 | 20,384,477,226 |
| Ms1995_007_Piomelli | 342,226 | 35,762,453,103 |
| Ms1997_003_Gottlieb | 463,619 | 51,004,022,325 |
| Ms1998_005_Zimbler (csv id: Ms1998_005) | 410,379 | 67,011,001,854 |

**14 of 24 not yet started** — see hand-off doc for the exact list and how to resume.

Per explicit user instruction, the job was stopped after these 10 finished/verified rather than continuing automatically to the rest.

## Notable process note

While this work was in progress, the user had a separate, unrelated `aws s3 sync` running in their own terminal (PID 93107) copying `s3://vtdlp-s3-tunnel-dev/iawa/` → `s3://vtdlp-pprd.img.cloud.lib.vt.edu/iawa/` — confirmed by the user to be an expected downstream sync from the staging/bastion bucket. Not touched by this session.
