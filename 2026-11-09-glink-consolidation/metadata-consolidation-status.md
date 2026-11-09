# GLink metadata consolidation status

**Date:** 2026-11-09
**Source directory:** `~/dev/dlp/assets/glink/docs`, which holds the metadata for `~/dev/dlp/assets/glink`

## TL;DR

- **Most comprehensive CSV:** `20261109_glink_consolidation_archive_metadata.csv`. It has 143 items and 35 columns, was last modified on Oct 9 at 06:44, and is the only archive file with a `size_source` column.
- **Already merged into it:** both earlier archive versions, the 41-row hand-measured sizes file, `missing.csv`, the scanning guide, the Dynamo/S3 inventory and `done.txt`. The archive-level alt text and visual description edits from the review file are also in it.
- **Still to merge:**
  1. `20261009_glink_computed-sizes_multi_archive_metadata.csv`: sizes for sketchbooks 001001 and 001002.
  2. `20261009_glink_extracted_dates.csv`: 297 page dates across 55 items. The master has no date column yet.
  3. The page-level description CSVs (`glink001001.csv`–`glink001010.csv`, `glink002121.csv`, `glink002128.csv`). These cover the 12 multi-page items, which are the only ingested items whose `alt_text` and `visual_description` are empty in the master.
- **One conflict to settle:** for `glink002001` the master has a height of **7.75 in**, but the computed-sizes file says **7.5 in** ("Physically measured 10 x 7.5 in").

---

## 1. What has been done (in date order)

| Date | File | Rows | What it is |
|---|---|---|---|
| Oct 5 | `glink_scanning_guide.csv` | 102 | Earlier export of the capture log (the scanning guide). Superseded. |
| Oct 5 | `glink_scanning_guide_.csv` | 143 | Fuller capture log: capture person, date, device, target, count, and hand-measured W×H for 87 items. Has no rows for s7–s10. |
| Oct 5 | `20261005_archive_consolidation.csv` | 143 × 34 | **First consolidated archive file.** Joins the scanning guide, Dynamo, S3/manifests, the template CSV and `done.txt`. Adds item-level `alt_text` and `visual_description` for 127 single-image items, plus `consolidation_notes` explaining each conflict. |
| Oct 5 | `20261005_archive_consolidation_review.csv` | 140 | QC pass on the alt text and visual descriptions (confidence %, issues, suggested correction). |
| Oct 5–7 | `glink001001.csv` … `glink001010.csv`, `glink002121.csv`, `glink002128.csv` | 2–89 each, 409 pages in all | **Page-level** `alt_text` and `visual_description` for the 10 sketchbooks, the 2-page beach painting (002121) and the 7-image silhouette set (002128). |
| Oct 5–6 | `glink0*_review.csv` | one per page CSV | QC pass on each page-level CSV. |
| Oct 7 | `20261109_glink_consolidation_archive_metadata.csv` | 143 × 35 | **Current master.** Adds the `size_source` column and fills in more sizes (see §3). |
| Oct 7 | `20261007_glink_archive_metadata_review.csv` | 140 | Byte-for-byte identical to the Oct 5 review file. It is a renamed copy, not a new review. |
| Oct 8 | `20261008_glink_no_size_archive_metadata.csv` | 143 × 34 | The master without the size columns' contents: `width_in` and `height_in` are blank except for hand-measured values, and there is no `size_source`. It looks like the input for the size computation. Otherwise identical to the Oct 5 file. |
| Oct 8–9 | `20261008_glink_computed-sizes_archive_metadata.csv` | 41 | Sizes for 41 paintings, with raw computed values, confidence and notes. |
| Oct 9 | `20261009_glink_computed-sizes_multi_archive_metadata.csv` | 2 | Sizes for sketchbooks 001001 (7×9 in, at 418 ppi) and 001002 (5.5×8.5 in, at 423 ppi), scaled from the pitch of the spiral wire. |
| Oct 9 | `missing.csv` (no header) | 4 | Archive rows for glink002140–002143: captured but not in Dynamo or S3. |
| Oct 9–10 | `20261009_glink_extracted_dates.csv` | 297 | Dates read from the images (`date_as_written`, `date_normalized`, `confidence`) for 55 items. Confidence: 258 high, 31 medium, 8 low. |

Other reference files:
- `done.txt`: a listing of the scanned TIFFs.
- `../glink_template_archive_metadata.csv`: 139 placeholder rows.
- `../glink_collection_metadata.csv`: the collection-level record.
- `DIL_file_naming_convention.docx`, `gretchen_link_*` guides.

## 2. Most comprehensive CSV

**`20261109_glink_consolidation_archive_metadata.csv`**

- All 143 items: 139 in Dynamo and S3, plus 4 not yet ingested (002140–002143).
- Format counts: 130 paintings, 10 sketchbooks, 2 photos, 1 silhouette set.
- It is a strict superset of the other two archive versions. Compared with them, only `width_in` and `height_in` differ, and the master has the extra `size_source` column.

How fully each column is filled (out of 143):

| Filled | Columns |
|---|---|
| All 143 | identifier, source_identifier, title, format, page_count, project, capture_*, in_dynamo, in_s3, in_template_csv, consolidation_notes |
| 139 | page1 px dims, ark, dynamo_id, dynamo_title, manifest_url, thumbnail_path |
| 140 | guide_count |
| 138 | sticker_identifier |
| 129 | source_tiff_files |
| 127 | alt_text, visual_description, width_in, height_in, size_source |
| 95 | medium |
| 2 | handling_notes |
| 1 | volume |
| **0** | **description, sensitive_content, content_note** |

`size_source` breakdown: 87 "measured by hand", 40 "computed from image at 400 ppi", 16 blank.

## 3. Already merged into the master

| Source | Evidence |
|---|---|
| `20261005_archive_consolidation.csv` | Same 143 IDs. Every non-size field is identical. |
| `20261008_glink_no_size_archive_metadata.csv` | Same as above. It is the size-stripped variant of the same data. |
| `glink_scanning_guide_.csv` (and the older `glink_scanning_guide.csv`) | Capture fields, counts and titles were pulled in. The only differences are intentional (see the notes below). |
| `20261008_glink_computed-sizes_archive_metadata.csv` | 40 of 41 rows match on width, height, px dims and `size_source`. **Exception: glink002001** (see §5). |
| `missing.csv` | All 4 rows (002140–002143) appear in the master with every field identical. |
| `20261005/20261007_..._review.csv` (archive-level) | The suggested corrections are in the master text. A string check matched 39 of 45 rows outright. Of the other 6, I checked 4 by hand and they are applied with small punctuation differences (for example `'78` vs `78`). The remaining 2 are for 002128, which is handled at page level. |
| Dynamo, S3, `done.txt`, template CSV | Recorded in `ark`, `dynamo_*`, `manifest_url`, `thumbnail_path`, `in_*`, `source_tiff_files` and `consolidation_notes`. |

Notes on how the master differs from the scanning guide on purpose:
- Sketchbook titles are normalized: `s1` → `Sketchbook 1`.
- Where the guide count and the S3 page count disagree, the S3 count is used, and the conflict is recorded in `consolidation_notes`.
- glink002086 and 002087 have width and height swapped relative to the guide: 18×24 and 20×24 instead of 24×18 and 24×20. This looks like an orientation correction, but **it is worth confirming**.

Page-level review CSVs: the page CSVs are newer than their review files. Spot checks show the suggestions were applied to the page CSVs, often with different wording. Because the wording differs, a string comparison can't confirm all of them automatically.

## 4. Still needs to be merged

### 4a. `20261009_glink_computed-sizes_multi_archive_metadata.csv`
- It covers glink001001 (7 × 9 in) and glink001002 (5.5 × 8.5 in). Both have blank `width_in`, `height_in` and `size_source` in the master.
- It was created about 2.3 hours after the master was last saved, so it is definitely not merged.
- Only 2 of the 10 sketchbooks are done. **Sketchbooks 001003–001010 still need size computation**, as do 002121 and 002128.

### 4b. `20261009_glink_extracted_dates.csv`
- 297 page-level dates across 55 items: all 10 sketchbooks and 45 paintings or photos.
- The master has **no date column**, so a target schema has to be chosen first. For example: an item-level `date_created` (a single date or a range taken from the pages), with the page-level dates kept in a page table.
- 8 low-confidence and 31 medium-confidence rows should be reviewed before merging.

### 4c. Page-level alt text and visual descriptions
These files have no counterpart in the master:

| Item | Page CSV rows | Master alt_text / visual_description |
|---|---|---|
| glink001001–001010 (sketchbooks) | 51, 58, 89, 50, 64, 14, 43, 5, 7, 19 | empty |
| glink002121 (Beach w/ umbrellas) | 2 | empty |
| glink002128 (Silhouettes) | 7 | empty |

They are the only 12 ingested items with empty `alt_text` and `visual_description` in the master; the other 4 empty items are the uningested 002140–002143. Two things need deciding:
- **Item level:** use the page-1 (cover) text as the item-level alt text and visual description, or write a new item-level summary.
- **Page level:** keep the page CSVs as a separate page table, or combine them into one `glink_page_metadata.csv`.

## 5. Conflicts and open items

1. **glink002001 height:** the master says 10 × **7.75**. The computed-sizes file says 10 × **7.5**, with the note "Physically measured 10 x 7.5 in; image estimate agreed." One of them needs correcting.
2. **Remaining items with no size (16):**
   - Sketchbooks 001001–001010. 001001 and 001002 are covered by the multi file.
   - 002121 and 002128.
   - The uningested 002140–002143.
3. **Columns that are entirely empty:** `description`, `sensitive_content`, `content_note`. Also `medium` is missing for 48 items.
4. **Not yet ingested:** glink002140–002143. Their rows come from `missing.csv` and are in the master. Separately, `../not-ingested/` holds `lgpst002147.tif` and `lgpst002148.tif`, which have **no rows anywhere**.
5. **Redundant files that could be archived:** `20261007_glink_archive_metadata_review.csv` is a duplicate of the Oct 5 review. `glink_scanning_guide.csv` is superseded by `glink_scanning_guide_.csv`. `20261005_archive_consolidation.csv` and `20261008_glink_no_size_archive_metadata.csv` are superseded by the master.

## 6. Suggested next steps

1. Settle the glink002001 height (7.5 or 7.75 in).
2. Merge the multi-sizes file into the master for 001001 and 001002.
3. Compute sizes for sketchbooks 001003–001010, 002121 and 002128.
4. Decide how to handle item-level vs page-level text for the 12 multi-page items, then merge the page CSVs.
5. Add a date column (or columns), review the low and medium confidence dates, then merge the extracted dates.
6. Write the merged result as a new dated master, for example `202611xx_glink_archive_metadata.csv`, and keep the Oct 7 file as a snapshot.

## 7. Update: files reorganized (2026-11-09)

- The user renamed the master `20261007_glink_archive_metadata.csv` to **`20261109_glink_consolidation_archive_metadata.csv`**. The references above now use the new name.
- These files are already merged into the master, or were intermediate inputs to it, so they were moved to `docs/merged/`:
  - `20261005_archive_consolidation.csv`, `20261005_archive_consolidation_review.csv`
  - `20261007_glink_archive_metadata_review.csv` (a duplicate of the Oct 5 review)
  - `20261008_glink_no_size_archive_metadata.csv`, `20261008_glink_computed-sizes_archive_metadata.csv` (the glink002001 height conflict is still open)
  - `missing.csv`, `glink_scanning_guide.csv`, `glink_scanning_guide_.csv`, `done.txt`
- These files stay in `docs/` because they still need to be merged:
  - `20261009_glink_computed-sizes_multi_archive_metadata.csv`
  - `20261009_glink_extracted_dates.csv`
  - `glink001001`–`001010`, `glink002121` and `glink002128` page CSVs, with their `_review.csv` files
- Left in place because they are reference documents, not metadata CSVs: `DIL_file_naming_convention.docx`, `gretchen_link_digitization_guide.xlsx`, `gretchen_link_scanning_guidelines.docx`.

## 8. Update: glink002001 height resolved (2026-11-09)

- The user confirmed that glink002001 is landscape and that its height is **7.75 in** (10 × 7.75 in). Every file already recorded it as landscape.
- The master was already correct.
- Fixed `merged/20261008_glink_computed-sizes_archive_metadata.csv`: `height_in` changed from 7.5 to 7.75, and `size_notes` from "10 x 7.5 in" to "10 x 7.75 in". The file's Windows-style (CRLF) line endings were kept.
- The conflict in §5 item 1 is now **resolved**.

## 9. Update: multi computed-sizes merged (2026-11-09)

- Merged `20261009_glink_computed-sizes_multi_archive_metadata.csv` into `20261109_glink_consolidation_archive_metadata.csv`. This filled `width_in`, `height_in` and `size_source` for:
  - glink001001: 7 × 9 in, "computed from image at 418 ppi (scale from spiral wire pitch)"
  - glink001002: 5.5 × 8.5 in, "computed from image at 423 ppi (scale from spiral wire pitch)"
- The pixel dimensions on page 1 matched the master. The target cells were empty beforehand.
- Only those 2 rows changed. The rest of the file was checked to be byte-for-byte identical, including its Windows-style (CRLF) line endings.
- The detailed `size_notes`, raw values and confidence were **not** carried over. The master has no columns for them, and the earlier 41-row size merge didn't carry them over either. They remain in the source file.
- Moved the source file to `docs/merged/`.
- **14 items still have no size:**
  - Sketchbooks glink001003–001010. Note that the multi-file notes say these sketchbooks were shot on the Phase One at about 415–425 ppi, not at the 400 ppi used for the i2s Quartz records.
  - glink002121 and glink002128
  - The uningested glink002140–002143

## 10. Update: printed cover sizes merged (2026-11-09)

The user noted that the sketchbook covers have their sizes printed on them. They confirmed that printed sizes follow the width × height convention, that they are accurate enough to use, and that 001003 and 001005 are 5.5 × 8.5 in (portrait). They also accepted the computed 7 × 9 in for 001001.

I merged the following into `20261109_glink_consolidation_archive_metadata.csv` with `size_source` = **"printed on cover"**. Only these 7 rows changed; the rest of the file is byte-for-byte identical and keeps its CRLF line endings.

| Item | W × H (in) | Page 1 px |
|---|---|---|
| glink001003 | 5.5 × 8.5 | portrait |
| glink001004 | 5.5 × 8.5 | portrait |
| glink001005 | 5.5 × 8.5 | portrait |
| glink001006 | 4 × 6 | **landscape (2856 × 1963)**: conflicts with the printed orientation |
| glink001007 | 9 × 12 | portrait |
| glink001008 | 15 × 22 | portrait |
| glink001009 | 16 × 12 | landscape |

**Open:** for glink001006, the page-1 scan and the visual description ("small spiral-bound sketchbook in landscape format") are both landscape. The pixel ratio of 1.45 is close to 6:4. So this pad's printed "4" X 6"" probably doesn't follow the width × height convention, and the value should likely be 6 × 4. I asked the user to confirm.

**Still without a size:** glink001010 (no cover scanned), glink002121, glink002128, and glink002140–002143.

## 11. Update: sizes for 001010, 002128, 002121 (2026-11-09)

| Item | W × H (in) | size_source | Notes |
|---|---|---|---|
| glink001010 | 14 × 17 | provided by project staff | Given by the user. Page 1 is portrait (6152 × 7492 px), which is consistent. |
| glink002128 | 2 × 3 | provided by project staff | Given by the user. The scans (about 1830 × 1875 px) include the round wooden frame, so the pixels don't show the paper size. |
| glink002121 | 10.5 × 6.5 | computed from image at 400 ppi | Computed in this session (see below). |

**How glink002121 was computed:**
- I downloaded both IIIF images from CloudFront at full size, which is the same as the master's pixel dimensions. Both carry a 400 dpi tag and were captured on the i2s Quartz.
- I found the edges of the object against the dark background by checking brightness along about 40 lines across and 40 lines down each scan.
  - Front: 4210 × 2618 px, which is 10.53 × 6.54 in. A slightly larger backing layer shows at the top and right, with an outer extent of about 10.58 × 6.62 in.
  - Back (taped and wrapped in plastic): 4223 × 2619 px, which is 10.56 × 6.55 in.
- Rounded to the nearest ¼ in, as for the other computed sizes: **10.5 × 6.5 in** (landscape). Confidence is high, because the front and back agree to within 0.03 in.
- The script and images are in the session scratchpad and were not kept.

`size_source` value "provided by project staff" was chosen by the assistant. The user may want a different wording.

**Now every ingested item has a size.** The only items without one are the four uningested items glink002140–002143.

## 12. Update: glink002121 item-level text (2026-11-09)

- Copied `alt_text` and `visual_description` for page 1 (the front) from `glink002121.csv` into the master row for glink002121. Page 2, the taped backing board, was not used.
- Dropped the leading "Front of the work. " from the visual description. That phrase only makes sense alongside the back page, and no other item-level description in the master has such a prefix.
- Left the `description` column empty, as it is for every other item.
- `glink002121.csv` and `glink002121_review.csv` stay in `docs/`, since the full page-level text isn't merged yet. Still without item-level text: glink002128 and the sketchbooks 001001–001010.

## 13. Update: glink002121 fully merged (2026-11-09)

- The user said the back image (page 2) can be ignored, so glink002121 counts as fully merged: size, alt text and visual description are all in the master.
- Moved `glink002121.csv` and `glink002121_review.csv` to `docs/merged/`. The extracted-dates file has no rows for 002121.
- No other files became fully merged in this step.
- **Still in `docs/` to merge:**
  - `20261009_glink_extracted_dates.csv`
  - the `glink001001`–`001010` page CSVs, with their review files
  - `glink002128.csv` and `glink002128_review.csv`

## 14. Update: extracted dates merged (item level)

Added four columns to the master after `visual_description`: `date`, `date_as_written`, `date_confidence`, `date_notes` (master now 39 columns). 55 of 143 items now have a date.

- **Single-image items (45):** values copied directly from `20261009_glink_extracted_dates.csv`. `date` is the EDTF-style `date_normalized` (e.g. `1980-05`, `195X`, `XXXX-07-21`), and `date_notes` holds the extraction note, including alternative readings.
- **Sketchbooks (10):** `date` is the earliest/latest year across high- and medium-confidence pages, e.g. `1934/1937`. Low-confidence readings are not counted. `date_confidence` is `high` when both endpoint years are supported by a high-confidence page. These pages were excluded as out of sequence or later additions:
  - 001001: '76 (p49) and Sept 2011 (p50)
  - 001005: 1971 (p24)
  - 001007: June 77 (p41) and June '97 (p42), both loose inserts
- **glink001008:** the only reading is low confidence ('88, could be 68/86/66), so it is kept as `1988`/low with the note.
- **glink001006:** 1985/2000 (medium). The 2000 comes from a single medium-confidence page.

Per the user, page-level dates for sketchbook images go in separate files. Wrote `docs/glink001001_dates.csv` … `glink001010_dates.csv`, which together hold 252 rows with the same columns and CRLF line endings as the source. Combined with the 45 single-image rows in the master, that covers all 297 source rows. Sketchbook `date_notes` in the master now point to `<id>_dates.csv`. `20261009_glink_extracted_dates.csv` moved to `merged/`.
