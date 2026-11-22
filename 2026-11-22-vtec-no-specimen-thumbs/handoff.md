# Hand-off: VTEC records without specimen thumbnails

## State

- `~/dev/dlp/assets/vtec/meta/20261122_vtec_no_specimen_thumbs.csv` lists the 128 records whose site thumbnail is not an IIIF specimen tile. Its columns are `identifier,url,title`.
  - 70 show a 3D render as their thumbnail.
  - 58 show the site's fallback image.
- It's committed on `main` as `f849ed8`. It has **not been pushed**.
- `media/thumbs/new-thumbs` was not created. No specimen images exist for these records' own specimens in either bucket:
  - `s3://vtdlp-s3-tunnel-prod/federated/vtec/`
  - `s3://vtlib-store/federated/vtec/`
- Nothing has been uploaded to S3, and DynamoDB hasn't been changed.

## Where things are

| What | Location |
|---|---|
| 2D specimen masters (source of IIIF tiles) | `s3://vtlib-store/federated/vtec/<id>/Access/<id>.tif` (2,439) |
| Photogrammetry captures (turntable TIFF/NEF, greycard) | `s3://vtdlp-s3-tunnel-prod/federated/vtec/box_*/VTEC<id>_<CommonName>/` and `s3://vtlib-store/federated/vtec/3d/…` |
| 3D render thumbnails | `s3://vtdlp-s3-tunnel-prod/federated/vtec/3d/<id>/` |
| 2D metadata (identifier, title, Occurrence/Record IDs) | `s3://vtlib-store/federated/vtec/20241009_vtec_2d_archive_metadata.csv`, `vtec_archive_metadata.csv` |

## Open options (not started)

1. **Same-species thumbnails:** 14 of the 128 share a scientific name with 2D records that have Access images. One of those images could be used, resized to 250px wide. It would show a different specimen from the one the record describes. The 14 are:
   - VTEC000006069
   - VTEC000007895
   - VTEC000006087
   - VTEC000002057, VTEC000006077, VTEC000002116
   - VTEC000006066
   - VTEC000006094
   - VTEC000006081
   - VTEC000006095
   - VTEC000006086
   - VTEC000006079
   - VTEC000006078
   - VTEC000006065
2. **Turntable frames:** 95 records have photogrammetry frames that could be cropped into a thumbnail. They have no scale or colour reference.
3. **Placeholder titles:** about 60 records on the site use their identifier as the title. Common names are in the capture folder names (e.g. `VTEC000006044_Orange-PatchedSmokeyMoth`) and could help fix them.
4. **Test tile:** one IIIF thumbnail on the site uses a tile named `VTEC…test-1`, which is worth checking.
