# Hand-off: glink002 date extraction (resume at glink002061)

## Goal

Inspect every image belonging to the `glink002***` records in
`~/dev/dlp/assets/glink/docs/20261007_glink_archive_metadata.csv` for written dates
(full or partial) and append the findings to
`~/dev/dlp/assets/glink/docs/20261009_glink_extracted_dates.csv`.

## State

- Done: glink002001–glink002060 (60 images, 4 batches). 20 dated rows appended.
- Remaining: 76 images, glink002061–glink002129, including the 2 pages of glink002121
  and the 7 pages of glink002128.
- Cannot be inspected: glink002140–143. They have no S3 assets and no local copies.
- The output CSV now has 272 data rows (252 for glink001, 20 for glink002).
- `~/dev/dlp/assets/glink` is not a git repository, so nothing there was committed.

## Why the job stopped

The first 60 images used more than 90% of the session limit. The user stopped the run
after batch 04 and is waiting for the limit to reset. The remaining work should use the
cheaper approach below, not the one used so far.

## Recommended approach for the remaining 76

These were proposed to the user and well received, but not explicitly approved and not
tested. Confirm before running, and consider a single 5-image trial batch first so the
real usage is known.

1. Pre-crop with a script, with no model involved. For each image produce one small
   overview (about 800 px on the long side) and full-resolution crops of the bottom
   strip and the four corners. Dates nearly always sit beside the signature in a bottom
   corner. The agent then reads two or three images per artwork and does not hunt with
   many crop calls.
2. Use about 5 images per sub-agent, not 15. Each tool call re-reads everything already
   in the agent's context, so late images in a large batch cost far more than early ones.
3. Run the first pass on Sonnet (the Agent tool takes a `model` parameter) and send only
   ambiguous digits to Opus for a second look.
4. Keep the user's original constraints: no more than 15 images per agent, one agent at
   a time, local images whenever possible.

Known trade-off: a fixed crop set misses a date written somewhere unusual. glink002054
had its date alone in the lower margin, away from the signature. The four-corner crops
cover most such cases; tell the agent to request an extra crop when the overview shows
writing elsewhere.

## Files

Copied into `resume/` in this directory, because the originals are in a temp location:

- `resume/batches/batch05.txt` … `batch10.txt` — the remaining images, 15 per file
  (batch10 has 1). Each line: `image_id | full size px | scale | format | medium | title`.
  Re-split these if using 5 per agent.
- `resume/results/batch01.csv` … `batch04.csv` — one row per inspected image, including
  the `none` rows with notes on which areas were checked. The `none` rows are not in the
  main CSV.
- `resume/INSTRUCTIONS.md` — the brief each sub-agent was given. It contains absolute
  paths into the old scratchpad; update them before reuse.
- `resume/append.py` — validates a batch result file against its batch list and appends
  only the dated rows. Usage: `python3 append.py <scratch_dir> <NN>`. It refuses to
  append a batch twice.
- `resume/crop_a.swift` — source of the crop tool
  (`crop_a <src> <dst> <x> <y> <w> <h>`, full-resolution pixels). Compile with
  `swiftc crop_a.swift -o crop_a` if the binary is gone.

Image caches, all under `/private/tmp/claude-502/-Users-whunter-dev-dlp-assets-glink/`
and liable to be cleaned up by the system:

- Full resolution, all 136 glink002 images:
  `150dfe01-5fd3-4556-997f-fb5264712264/scratchpad/full/<image_id>.jpg`
- 1568 px view copies:
  `6151b018-cc84-4238-8d1e-ecd46599c571/scratchpad/glink002/view/<image_id>.jpg`
- Crop tool binary: `6151b018-cc84-4238-8d1e-ecd46599c571/scratchpad/crop_a`

If the caches are gone, the source is
`s3://ingest-dev.img.cloud.lib.vt.edu/federated/glink/`.

## Conventions to keep

- Columns: `identifier,page,image_id,date_as_written,date_normalized,confidence,notes`.
- The main CSV holds only images where a date was found. Images with no date get no row.
- `date_as_written` is transcribed exactly, including apostrophes and the artist's
  spelling. Two-digit years are read as 19xx.
- Numbers that are part of the depicted scene, inventory stickers (`lgpst…`), and
  circled sheet numbers are not dates; mention them in the notes.
- A date in the catalogue title that is not written on the work is not recorded
  (glink002027, "Portrait from Art Class 1992").

## Open items for the user

- Three medium-confidence readings to review: glink002008 (month "Ju", June or July),
  glink002031 (Feb '80, alternative '50), glink002052 (77, alternative 79).
- For signed works with no date beside the signature, most agents cropped only the
  signature area at full resolution. A date far from the signature could have been
  missed on those; the affected images are identifiable from the notes in
  `resume/results/`.
