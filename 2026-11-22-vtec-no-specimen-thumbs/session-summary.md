# Session summary: VTEC records without specimen thumbnails

**Date:** 2026-11-22
**Repo:** `~/dev/dlp/assets/vtec` (branch `main`, not pushed)

## What was done

### 1. Listed records that have no "specimen" thumbnail

The collection is https://digital.lib.vt.edu/collection/12bc124a.

- I read all 26 listing pages (2,568 records) in Chrome, at 100 results per page.
- I grouped the records by card thumbnail URL. The user confirmed that specimen thumbnails are IIIF tiles.
  - **2,440 are IIIF tiles:** `img.cloud.lib.vt.edu/federated/vtec/tiles/VTEC…-1/full/250,/0/default.jpg`. One tile is named `VTEC…test-1`.
  - **70 are 3D-render PNGs:** `…/federated/vtec/VTEC…/3d/HighRes_VTEC…_thumbnail.png`.
  - **58 use the site fallback:** `digital.lib.vt.edu/images/fallback_thumbnail.jpg`.
- For the 128 records that aren't IIIF, I read each identifier from its detail page, loading the pages in same-origin iframes.
- **Output:** `meta/20261122_vtec_no_specimen_thumbs.csv` (columns `identifier,url,title`, 128 rows), committed as `f849ed8`.
- The user had first asked for sub-agents working in batches of 100. Once the IIIF pattern was clear, they chose to skip the sub-agents.

### 2. Searched S3 for specimen images of those 128 records

The user asked for a title-based first pass, then an image check. Matches were to go to `media/thumbs/new-thumbs` at 250px wide.

- **`s3://vtdlp-s3-tunnel-prod/federated/vtec/`** (199,520 keys):
  - There are no 2D specimen photos in this bucket. Its folders are photogrammetry captures: `box_*/VTEC<id>_<CommonName>/`, holding about 364 TIFF/NEF turntable frames, a greycard, masks and models. Its `3d/<id>/` folders hold renders.
  - 95 of the 128 have a capture folder. The other 33 have renders only.
  - Title and common-name matching found no other folders for the 33.
  - I looked at sample frames of VTEC000006069 (frames 0001 and 0200, plus the greycard). They show the specimen on a pin in a clamp, with no scale or colour reference.
- **`s3://vtlib-store/federated/vtec/`** (182,159 keys):
  - The 2D specimen masters are here: `federated/vtec/<id>/Access/<id>.tif`, 2,439 of them, matching the IIIF tiles.
  - None of the 128 has an Access image.
  - Occurrence/Record ID matching: 77 of the 128 had IDs. None of them matched a 2D record, so none of the 128 was also photographed in 2D under another ID.
  - Title matching: 14 records share a scientific name with 2D records, but those are different specimens of the same species.
  - The 35 of the 128 that have `3d/` folders here contain nothing new: only turntable frames, greycards and `Thumbs.db`.
- **Result:** I found no specimen image of any of the 128 records' own specimens. The user chose to stop, so nothing was copied to `new-thumbs`.

## Notes

- I didn't pull API config out of the site's JS bundle; the auto-mode classifier blocked that. Listing was done through the browser UI instead.
- Posting data from the page to a localhost receiver stalled, probably on Chrome's local-network permission. I read the data back in chunks instead.
- Data quality on the site:
  - About 60 records have the identifier as their title (e.g. `VTEC000006044`).
  - Two titles have broken characters: "H√ºbner" and "Herrich-Sch√§ffer".
