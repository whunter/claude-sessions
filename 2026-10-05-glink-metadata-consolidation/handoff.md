# Hand-off: glink metadata consolidation

## State

`~/dev/dlp/assets/glink/20261005_archive_consolidation.csv` is written and complete for what the existing materials support. Nothing was changed in DynamoDB or S3; all AWS access was read-only. The `glink` directory is not a git repository, so the CSV is not under version control.

## Where things live

- **Collection:** `glink`, Dynamo collection id `07bc52cc-a44d-4488-b28d-e19d4e03cc22`, ARK `ark:/53696/212bf5e7`
- **Hosted:** https://dev.d1n265krqy0ld3.amplifyapp.com/collection/212bf5e7
- **Dynamo tables:** `Archive-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev`, `Collection-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev` (us-east-1)
- **S3:** `s3://ingest-dev.img.cloud.lib.vt.edu/federated/glink/`, served through `d21nnzi4oh5qvs.cloudfront.net`
- **Identifier scheme:** scanning guide uses `lgpst…`; hosted records use `glink…` with the same digits. `001xxx` are sketchbooks, `002xxx` are paintings, photos and silhouettes.

## Things to know before continuing

- The `gsi-Collection.archives` index returns nothing for this collection (`collectionArchivesId` is not set on these records). Find the archives by scanning on `identifier` containing `glink`, or by the `collection` attribute.
- Tiles are static IIIF level 0. Only the sizes listed in each `info.json` exist, so thumbnail widths vary per image (e.g. `182,`, `250,`); an arbitrary width will fail to load.
- `build_consolidation.py` expects two files in a scratch directory passed as its argument:
  - `arch_scan_plain.json`: the Dynamo archive items, deserialized to plain JSON
  - `man_dims.json`: `{identifier: [[width, height], …]}` per canvas, taken from each `<identifier>/manifest.json` in S3

## Open decisions for the collection owner

1. **Descriptions, alt text, visual descriptions:** all blank. Nothing in the existing materials supplies them.
2. **Sketchbook titles:** currently "Sketchbook 1"–"Sketchbook 10". Confirm or replace, and confirm the s1–s10 order matches `glink001001`–`010`.
3. **`glink002121`:** four TIFFs were captured but two pages are hosted. Decide whether the other two belong in the record.
4. **`glink002140`–`143`:** captured but never ingested. Source TIFFs are not listed in `done.txt`.
5. **Collection description:** Dynamo and the CSV disagree on the artist's death year (2018 vs 2015) and the date range of works (1934-2015 vs 1934-2012). `glink/info.yml` says 1934-2015.
6. **Missing medium and dimensions:** 48 rows lack medium, 56 lack dimensions. These need the physical items or the capturer's notes.
7. **Test records:** `glink002121_test` and `glink002121_refactored` are visible in the dev collection in Dynamo; `glink001001_test` exists in S3 only. Remove if no longer needed.

## Suggested next steps

- Fill the open items above in the consolidated CSV, then derive a new archive metadata CSV (identifier, title, description, alt_text, visual_description) from it to replace the placeholder template and re-ingest.
- Reduce the three scanning guide CSVs and the duplicated `.xlsx`/`.docx` files to one copy each once the consolidated file is accepted.
