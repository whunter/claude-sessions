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

## 15. Update: glink001006 size confirmed

The user confirmed that glink001006 stays at 4×6 (width_in=4, height_in=6) despite the landscape scan. No change to the master.

## 16. Missing-field summary (master, 143 items)

| Field | Missing | Painting (130) | Sketchbook (10) | Photo (2) | Silhouette (1) |
|---|---:|---:|---:|---:|---:|
| title | 0 | 0 | 0 | 0 | 0 |
| description | 143 | 130 | 10 | 2 | 1 |
| date | 88 | 85 | 0 | 2 | 1 |
| alt_text | 15 | 4 | 10 | 0 | 1 |
| visual_description | 15 | 4 | 10 | 0 | 1 |

- **alt_text and visual_description** are missing for the same 15 items:
  - 001001–001010: page-level text exists in `glink0010NN.csv`.
  - 002128: the silhouette; `glink002128.csv` exists.
  - 002140–002143: the uningested paintings.
- **date:** the 88 items have no date in the extraction, either because no inscription was found or because the item was not processed.

## 17. Update: glink002128 merged

- glink002128 (Silhouettes, 7 images) now has an item-level `alt_text` and `visual_description` in the master.
- The visual description summarizes all seven pages from `glink002128.csv`:
  - two framed silhouettes with "GL" monograms
  - five unframed
- The review CSV's only suggestions (pp1–2) confirm the existing "GL" monogram wording, so there were no corrections to apply.
- Only the 002128 row changed.
- `glink002128.csv` and `glink002128_review.csv` moved to `merged/`.
- Items still missing alt_text and visual_description: 14 (001001–001010, 002140–002143).

## 18. Update: individualized alt text for glink002128

- Wrote `docs/glink002128_alt_text.csv` (identifier, page, image_id, alt_text; CRLF) with one unique alt text per image (pp1–7).
- Each one gives:
  - framed or unframed
  - gender and facing direction
  - distinguishing features: headwear, hair, collar or jabot, paper or frame condition, GL monogram
- Each ends with `silhouette: #n`.
- There are no group or count references.
- Based on the page-level text in `merged/glink002128.csv`.
- The master's group-level alt_text is unchanged.

## 19. Update: glink002128 master alt_text points to file

Master `alt_text` for glink002128 is now `path: glink002128_alt_text.csv`, relative to the master's directory (`docs/`). The previous group-level alt text was replaced. visual_description is unchanged.

## 20. Update: sketchbook alt_text/visual_description point to page files

For the 10 sketchbooks (001001–001010), master `alt_text` and `visual_description` now read `path: glink0010NN.csv`, relative to `docs/`. Those page-level files and their `_review.csv` files stay in `docs/` so the references resolve. Items still missing alt_text/visual_description: 002140–002143 only.

## 21. Update: sketchbook review files moved

Moved `glink001001_review.csv` … `glink001010_review.csv` to `merged/`. The page-level files `glink0010NN.csv` stay in `docs/` because the master references them.

## 22. Update: Nag's Head titles disambiguated

Appended the date to the duplicate "Nag's Head" titles: glink002008 → "Nag's Head, 1977" (date confidence medium; inscription 'Ju 77'), glink002054 → "Nag's Head, 1994" (high).

## 23. Update: medium value normalized

Changed medium "colored marker?" → "marker" (1 item). Medium is populated for 95/143 items (all paintings).

## 24. Update: uningested items removed

Removed glink002140–002143 from the master: Dogwood Tree; House w/ gate (Birthday card); Dog and Cat in Window (Birthday card); Birdhouse and Flowers. They were captured 2026-01-30 per the scanning guide but have no Dynamo record, S3 assets or images. The master now has 139 items. Their scanning-guide rows still exist in `merged/glink_scanning_guide*.csv` if they are needed later.

## 25. Update: medium filled for all items

- A sub-agent proposed medium values for the 44 remaining blank items. It calibrated on the existing values, viewed the `media/scaled` images, and for sketchbooks also used the page text.
- The proposals, with confidence and evidence for each item, are in `medium_proposals.csv` in this folder. All 44 were merged; medium is now filled for 139/139 items.
- **Values merged:**
  - oil/acrylic 23
  - watercolor 6
  - pen/colored pencil 3
  - pen 2
  - pencil/pen 2
  - photograph 2
  - pencil, multiple, watercolor/pencil, pastel, pastel/watercolor and ink, 1 each
- **New terms:** `photograph` (002124, 002127) and `ink` (002128 silhouettes, judged brush-painted rather than cut; medium confidence).
- **Low confidence:**
  - 001010, pencil/pen: "multiple" is an alternative because a few pages are chalk, colored pencil or oil pastel.
  - 002116, oil/acrylic: could be pastel on velour paper.
- **Medium confidence:** 001005, 001006, 001009, 002123, 002128, 002129.

## 26. Update: 002128 medium confirmed

The user confirmed that the glink002128 silhouettes are ink (painted, not cut). The master value `ink` stands.

## 27. Update: 002116 medium confirmed

The user confirmed that glink002116 is oil/acrylic on velvet fabric, so the medium is unchanged. Corrected the support in the visual_description ("velvet-like fabric" → "velvet fabric") and in the date_notes ("hexagonal board" → "hexagonal velvet panel"; "gouache or oil still life on brown board" → "oil/acrylic still life on velvet fabric").

## 28. Update: 001010 medium

Changed glink001010 medium from pencil/pen to multiple, per the user.

## 29. Tags column

- Added a `tags` column to master right after `visual_description`. The master now has 40 columns.
- Tags were generated from the 536 scaled images in 54 batches of 10, one sub-agent per batch, using each image together with the title, alt_text and visual_description already in master.
  - Each image has 4–13 tags, lowercase and separated by `; `.
  - Tags leave out medium, dates and the artist's name.
- 127 single-image records have their tags written directly in master.
- 12 multi-image records reference a separate file instead, as `path: <id>_tags.csv` in docs/:
  - the sketchbooks glink001001–001010
  - glink002121 (2 images)
  - glink002128 (7 silhouettes)
- There are 1,082 distinct tags. The most common are sketch (322), architecture (191), tree (172) and landscape (115).
- The merge script is in `tags_merge.py`.

## 30. Aggregated tags and the `||` delimiter

- In master, the `tags` value of the 12 multi-image records is now the full list of unique tags from all pages, in order of first appearance. This replaces the `path: <id>_tags.csv` reference. The per-image `*_tags.csv` files are still in docs/.
- Multi-valued lists now use `||` as the delimiter instead of `;`. This applies to:
  - `tags` in master and in all 12 `*_tags.csv` files
  - `source_tiff_files` in master (2 records)
- Semicolons in prose fields are unchanged: visual_description, date_notes, consolidation_notes, and the notes column of the `*_dates.csv` files.

## 31. Tags trimmed to the top 15

- In master, the aggregated `tags` lists of the 12 multi-image records are now cut to the 15 most common tags.
  - "Most common" means the number of that record's images the tag appears on.
  - Ties are broken by order of first appearance.
- The per-image `*_tags.csv` files are unchanged.
- No single-image record had more than 13 tags, so none of them changed.

## 32. Tag counts exclude covers and versos

The top-15 tag lists for multi-image records were recalculated without cover and verso images.

- An image was left out if one of its tags contained "cover" (front, back or inside) or "verso". That came to 20 images: 19 sketchbook covers plus the 002121 verso.
- 6 master rows changed: 001004, 001006, 001007, 001008, 001009 and 002121.
- 002121 now has 10 tags, which is every tag on the front image.

## 33. Descriptions generated

- Every record in master now has a `description`: a short catalog-style summary, 139 in all. 139 lines changed, and the round-trip check passed before the edit.
- The work ran as 25 sub-agent batches, each using no more than 10 images. Waves of 5 ran one after another.
  - **Batches 1–13:** the 127 single-image records, up to 10 per batch.
  - **Batches 14–25:** one batch for each multi-image record. Each agent saw up to 10 images: page 1 plus pages spaced evenly through the item. It also read all the page-level files (alt text and visual description, `_tags`, `_dates`).
- The shared prompt is in `description_instructions.md` and the final text in `description_proposals.csv`.
- **User input during the run:**
  - 002044 shows Mary Baldwin University, Staunton VA. The description says so; the title still reads "(Mary Baldwin maybe?)".
  - All signatures are forms of Gretchen Hitt Link, usually "G Link". The 002116 description was softened to "faintly signed".
- **Edits after review:**
  - Took out a sentence in 002050 that pointed out the teapot/coffee pot mismatch.
  - Made Staunton and Mary Baldwin explicit in 002076, 002097 and 002108.
- **Lengths:** single-image descriptions are 30–95 words. Four multi-image descriptions run 162–174 words, a little over the 160 target: 001001, 001002, 001009 and 002128.
- **Discrepancies the sub-agents reported** (no metadata was changed):
  - **Titles:**
    - 002050 "Teapot" shows a coffee pot.
    - 002129 "Windmill (Holland?)" is inscribed "Portugal Oct 79".
    - 002040 "Albufura" should be Albufeira.
    - 002081 "Cemetary" is misspelled.
    - 002090 "Band 'Conservice'" probably means Concert.
    - 002098: the house number is 117 in the title, 112 in the image and 111 in date_notes.
    - 002122: "Eduardo Placido" isn't supported by anything in the image.
    - 002126 "Fruit" shows vegetables.
  - **Dates:**
    - 002070 '52 could be '82.
    - 002064 '45 could be '95.
    - 001006 p7 may read 2002, not 2000.
    - 001003 pp43–44 are dated '82 among 1983 Canterbury pages.
    - 001003 p40 reads "Canterbury", not "possibly Cambridge".
    - 001007 p42 is 1977 in the alt text but '97 in the dates file.
  - **date_notes or visual_description that don't match the image:**
    - 002013 date_notes says "watercolour", but the medium is marker (confirmed by the user).
    - 002078 date_notes lists a pot, tomatoes and driftwood; the image shows a bucket and apples.
    - 002077 date_notes says split-rail; the image shows a gate and wire fence.
    - 002025: the crookneck squash is probably a banana.
    - 002101: a dog in date_notes, a cat in visual_description.
    - 002095: date_notes says a jacket; the image shows a vest.
    - 002118: a pipe in alt text, a quill in date_notes.
    - 002031: brick in date_notes, stone in visual_description.
    - 002010: the legs aren't striped.
    - 002035: the "doorway" looks like a post.
  - **Medium or format:**
    - 002061 is a pencil sketch but has format "painting".
    - 001001 medium "pencil" leaves out its watercolor and ink pages.
    - 001006 also uses colored pencil.
  - **Privacy:** 002088's description names Leslie Hoy and William L. Hunter, taken from the invitation.
