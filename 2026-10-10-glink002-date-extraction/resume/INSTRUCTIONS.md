# Date extraction from Gretchen Link artwork scans

You are inspecting scanned artworks (paintings, sketches, cards, photos, silhouettes) by
Gretchen Link (signs "GLink", "Gretchen Link", earlier "Gretchen Hitt"; active roughly
1930s-2000s) to find any handwritten or printed dates, full or partial. The result feeds
an archival metadata spreadsheet, so a wrong date is worse than a missing one.

## Files (all local; do not download anything)

- Batch list: `SCRATCH/batches/batchNN.txt` (your batch number is in your task). One
  image per line: `image_id | full_width x full_height px | scale | format | medium | title`.
- View copy (longest side 1568 px): `VIEW/<image_id>.jpg`
- Full-resolution copy: `FULL/<image_id>.jpg`
- Crop tool: `CROP <src> <dst> <x> <y> <width> <height>` — coordinates are in
  full-resolution pixels, origin top-left. To convert a position you see in the view
  copy, multiply by the `scale` value on the batch line.
- Write crops to `SCRATCH/crops/` with names starting with the image_id.

Paths:
- SCRATCH = /private/tmp/claude-502/-Users-whunter-dev-dlp-assets-glink/f90c6e6b-e6d5-41cc-bc57-7ee07072a179/scratchpad
- VIEW = /private/tmp/claude-502/-Users-whunter-dev-dlp-assets-glink/6151b018-cc84-4238-8d1e-ecd46599c571/scratchpad/glink002/view
- FULL = /private/tmp/claude-502/-Users-whunter-dev-dlp-assets-glink/150dfe01-5fd3-4556-997f-fb5264712264/scratchpad/full
- CROP = /private/tmp/claude-502/-Users-whunter-dev-dlp-assets-glink/6151b018-cc84-4238-8d1e-ecd46599c571/scratchpad/crop_a

## Method, per image

1. Read the view copy with the Read tool and look at the whole thing.
2. Dates on these works are small and easy to miss at view size. They are usually next
   to the signature (most often lower right, sometimes lower left or bottom centre), and
   typically a two-digit year with an apostrophe (`'78`), sometimes with a month
   (`June '77`, `Jan '92`). Captions, inscriptions, mat or backing-board notes, stickers
   and labels can also carry dates. So always crop the signature area and any other
   writing from the full-resolution copy and read the crop. If you see no signature in
   the view copy, crop each of the four corners plus the bottom edge at full resolution
   before concluding there is no date. Keep crops under about 1600 px on a side so they
   are shown at native resolution.
3. If a digit is ambiguous, crop tighter and look again. Report what is actually
   written; if two readings remain plausible, give the likelier one, lower the
   confidence, and name the alternative in the notes.
4. Inspect every image in the batch yourself, one at a time. Do not delegate, and do not
   skip an image because its title makes a date seem unlikely.

## What counts

- Count: dates written or printed on the work, its mat, mount, or attached labels —
  including partial ones (year only, month and year, decade).
- Do not count: numbers that are part of the depicted scene (a year on a drawn building
  sign, a calendar in a still life, a house number), inventory or sticker identifiers
  such as `lgpst002045`, dimensions, prices, or the scanner colour target and ruler.
  If such a number could be mistaken for a date, mention it in the notes of that
  image's row (or of its `none` row) so a reviewer knows it was seen and excluded.
- If one image carries more than one distinct date, write one row per date.

## Output

Write `SCRATCH/results/batchNN.csv` (same NN as your batch) using a proper CSV writer
(python3 `csv` module) so quoting is correct. Header exactly:

    identifier,page,image_id,date_as_written,date_normalized,confidence,notes

- `identifier`: image_id without the page suffix (`glink002128-3` -> `glink002128`).
- `page`: the number after the hyphen.
- `date_as_written`: transcribed exactly as it appears, including apostrophes and
  punctuation (`'78`, `June·80`, `34-36`).
- `date_normalized`: ISO-style — `1978`, `1977-06`, `1992-01-14`; a range as
  `1934/1936`. A two-digit year is 19xx unless the work clearly says otherwise.
- `confidence`: `high`, `medium`, or `low`.
- `notes`: where on the work the date is, the writing medium, what it sits next to
  (e.g. under the 'GLink' signature), a brief description of the subject, and any
  alternative reading.

Every image in the batch must have at least one row. For an image with no date, write a
row with `date_as_written` = `none`, empty `date_normalized` and `confidence`, and notes
saying which areas you cropped and checked and whether a signature is present.

Example rows:

    glink001010,5,glink001010-5,June '77,1977-06,high,"Lower right, black ink, under the 'GLink' signature; ink drawing of a building whose drawn doorway sign reads 'SMA MESS HALL 1913' (sign not counted as a date)"
    glink001010,14,glink001010-14,'78,1978,medium,"Bottom centre-right, pencil, after the 'GLink' signature; second digit is a closed top loop with a crossed tail, read as 8 (alternative 9, i.e. 1979); coloured pencil drawing of a toddler with toys"
    glink001010,7,glink001010-7,none,,,"Signature 'GLink' lower right with no date beside it; cropped all four corners and bottom edge at full resolution; no other writing"

## Final reply

Reply with a short plain-text summary only: how many images you inspected, how many
have dates, the image_ids whose reading you are unsure of, and any image you could not
inspect and why. The CSV file is the deliverable; do not repeat its rows in the reply.
