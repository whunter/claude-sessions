# Hand-off: alt text and visual descriptions for the Gretchen Link collection

## Current state

- Non-sketchbook records are finished and written to `/Users/whunter/dev/dlp/assets/glink/docs/`:
  - `20261005_archive_consolidation.csv` has `alt_text` and `visual_description` for 127 single-image records.
  - `glink002121.csv` (2 rows) and `glink002128.csv` (7 rows) hold the per-image descriptions for the two
    multi-image records.
- Sketchbooks are partly described but nothing for them has been written to the project directory. The user
  stopped the run and asked for the non-sketchbook results only.
- `/Users/whunter/dev/dlp/assets/glink` is not a git repository, so nothing there is committed.

## Files in this directory

| File | Contents |
| --- | --- |
| `session-summary.md` | What was done, method, conventions, caveats. |
| `descriptions_in_progress.tsv` | 299 rows, no header: `<identifier>-<page, 3 digits>`, alt text, visual description, tab separated. Covers every non-sketchbook image, sketchbooks 1 and 2 in full, and sketchbook 3 pages 1–54. |
| `image_urls.txt` | 536 lines: the CloudFront URL used for each page image and the local filename it was saved as. |

## To finish the sketchbooks

1. Ask the user whether they want the sketchbooks completed. They stopped the run without giving a reason.
2. Re-download the images: each line of `image_urls.txt` is `<url> <relative path>`, so
   `xargs -P 12 -n 2 sh -c 'curl -sf -o "$1" "$0"' < image_urls.txt` from a directory containing `img/`
   recreates the set.
3. Describe the remaining pages, appending to the TSV in the same three-column format:
   - `glink001003` pages 55–89
   - `glink001004` (50), `glink001005` (64), `glink001006` (14), `glink001007` (43), `glink001008` (5),
     `glink001009` (7), `glink001010` (19)

   That is 237 images.
4. Write one file per sketchbook, `docs/glink0010NN.csv`, with the same columns as `glink002121.csv`:
   `identifier, page, image_id, alt_text, visual_description`.

## Gotchas

- Tiles are static IIIF level 0. Only the widths listed in each `info.json` exist, and they differ per tile
  set. `image_urls.txt` already has a valid width for every page.
- Images at 600–1000 px wide are too heavy to view many at a time. Reducing them to a 760 px long edge with
  `sips -Z 760` allowed batches of about 18.
- The consolidation CSV now lives in `docs/`, not the collection root where it was first created.
- `glink002121` has 2 pages in S3 (front and back) although 4 TIFFs were captured. `glink002128` has 7.
- Several sketchbook pages are blank-looking mirror-image offsets of the facing drawing. Describe them as
  such.

## Open decisions for the collection owner

- Whether the sketchbook records should also get a record-level `alt_text` and `visual_description` in the
  consolidation CSV, in addition to the per-page files.
- Whether alt text needs a hard length limit. Delivered rows run up to 138 characters.
- Whether named sitters from the scanning-guide titles should appear in the descriptions. They are currently
  left out.
- When and how to load titles and descriptions into DynamoDB and the S3 metadata CSV, which still hold
  placeholders.
