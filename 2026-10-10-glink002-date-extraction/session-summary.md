# Session summary: glink002 date extraction

Date: 2026-10-10
Working directory: `~/dev/dlp/assets/glink`

## What was asked

Find the `glink002***` records in `docs/20261007_glink_archive_metadata.csv` whose
images had not yet been inspected for dates, split the images into batches of at most
15, process each batch with its own sub-agent one at a time, and append the record
identifier and extracted dates to `docs/20261009_glink_extracted_dates.csv`, using
locally cached images where possible.

## What was done

- Confirmed that all ten glink001 records were already in the dates CSV and that no
  glink002 record was.
- Found 133 glink002 records with 140 pages. Four records (glink002140–143) have no S3
  assets, leaving 136 images across 129 records.
- Found all 136 images already cached from earlier sessions, both at full resolution
  and as 1568 px view copies. Nothing was downloaded from S3.
- Found that an earlier session the same morning had prepared batch lists and cropped
  the first 15 images but never wrote results. All work was redone from the first image.
- Split the 136 images into 10 batches (nine of 15, one of 1), wrote a shared
  instruction file, and wrote a script that validates each result file against its batch
  list before appending.
- Ran batches 01–04 sequentially. The user then asked to stop after the running agent
  finished, so batch 05 was not started.

## Results

60 images inspected (glink002001–060): 20 with dates, 40 without.

| Batch | Records | Dated | Dates appended |
|---|---|---|---|
| 01 | glink002001–015 | 6 | 003 (1982), 007 (1988), 008 (1977), 012 (1980-05), 013 (1983), 015 (1990) |
| 02 | glink002016–030 | 6 | 023, 024, 025 (all 1990), 028 (1978), 029, 030 (both 1982-05) |
| 03 | glink002031–045 | 3 | 031 (1980-02), 033 (1990), 040 (1979) |
| 04 | glink002046–060 | 5 | 051 (1978), 052 (1977), 054 (1994), 055 (1978), 057 (1986) |

Medium-confidence readings, with the alternative recorded in the notes column:

- glink002008: year 77 is clear; the month is a two-letter abbreviation read as "Ju"
  (June or July), so it is normalized to the year only.
- glink002031: read as Feb '80; the first year digit could be a 5 (1950).
- glink002052: read as 77; the second digit is blobby pastel and could be a 9 (1979).

Following the file's existing convention, only images with a date were appended. The
per-batch result files keep a row for every image, including the undated ones.

## Checks

- Each batch result was validated before appending: every image in the batch list has a
  row, identifiers match image ids, and dated rows have a normalized date and a
  confidence value.
- The batch 03 agent reported that four of its "no date" calls (035, 038, 042, 043)
  rested on notes from an earlier pass. Those four were re-checked directly against the
  images and hold. The faint marks along the bottom of glink002042 are an illegible
  paper embossing, not writing.
- Not verified: the dated readings themselves were not independently re-read.

## Cost

The 60 images used more than 90% of the user's session limit.

| Batch | Tool calls | Duration |
|---|---|---|
| 01 | 59 | 3 min |
| 02 | 51 | 3 min |
| 03 | 425 | 22 min |
| 04 | 92 | 5 min |

Likely causes, as discussed with the user:

- Local caching saves download time but not tokens. The cost is the model reading
  images: roughly 2,500 tokens for a view copy and a similar amount for each crop.
- Every tool call re-reads the agent's whole context, so in a 15-image batch the later
  images cost far more than the early ones.
- Batch 03 lost its images from context several times and re-viewed them. It was
  probably the largest single consumer.
- All agents ran on Opus, including for routine "signature, no date" cases.

## Proposed changes for the remaining 76 images

Pre-crop with a script, use about 5 images per agent, run the first pass on Sonnet, and
shrink the overview image to about 800 px. The expected saving is several-fold; that is
an estimate, not a measurement. Details and the trade-off are in `handoff.md`.

## Files changed

- `~/dev/dlp/assets/glink/docs/20261009_glink_extracted_dates.csv` — 20 rows appended
  (252 → 272 data rows). That directory is not a git repository, so there is no commit.
- `resume/` in this directory — batch lists, per-batch results, the agent instructions,
  the append script, and the crop tool source, copied from the session scratchpad.
