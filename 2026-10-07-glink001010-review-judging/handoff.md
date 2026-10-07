# Hand-off: glink description review judging

Date: 2026-10-07

## State

- `~/dev/dlp/assets/glink/docs/glink001010.csv` has the judged corrections applied (pages 4, 8, 11, 12, 18). See `session-summary.md` for the exact changes.
- `docs/glink001010_review.csv` is unchanged and still shows the original issues and suggestions, including the ones that were rejected.
- The glink directory is not under git, so there is no commit or diff for the edit. Only the current file exists.

## Open items

- Page 4 date: now reads "79" in both fields. Worth a human look if certainty matters; the judge put it at about 90%.
- Optional addition for page 18: "a small bear stands at the far end of the table". Not applied, because it is an omission rather than an error.
- The same judging pass has not been run in this session for the other review files in `docs/` (glink001001 to glink001009, glink002121, glink002128). Their status was not checked here.

## How to repeat for another item

1. Read `docs/<item>_review.csv`; take the rows with non-empty `issues` or `suggested_correction`. Suggestions are " | " separated, each prefixed with the field it targets, and are replacement phrases, not whole fields.
2. Spawn judge agent(s), at most 50 images each, told to report only and not edit files.
3. Images are IIIF level-0 static tiles:
   - S3: `s3://ingest-dev.img.cloud.lib.vt.edu/federated/glink/tiles/<image_id>/`
   - HTTP: `https://d21nnzi4oh5qvs.cloudfront.net/federated/glink/tiles/<image_id>/full/full/0/default.jpg` (full resolution, about 7500 px, about 10 MB)
   - The `full/1200,/0/default.jpg` derivative returned AccessDenied for some pages; downscale from the full-resolution file instead.
4. Have the judge crop at full resolution for signatures, dates and small details, and return verbatim current phrase plus replacement for each upheld item, checking both fields for the same claim.
5. Apply with exact-match replacements (assert each phrase matches once) and confirm untouched rows are unchanged.

## Convention to pass to any reviewer or judge

`alt_text` uses standard spellings of words the artist misspelled; `visual_description` transcribes the artist's spelling exactly. The difference between the fields is intended and is not an error.
