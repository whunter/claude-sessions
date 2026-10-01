# Handoff: gen2 rejected-records and orphaned-archives CSVs (dlp-access Gen 2)

Follow-up to `../2026-09-30-item-inspection/`. This session only produced data files; nothing in `~/dev/dlp/access/dlp-access` changed (branch `gen2-main` is still 2 commits ahead of origin, unpushed), and no live index or table was modified.

## Outputs

Both are in `../2026-09-30-item-inspection/`:

- `gen2-opensearch-rejected-records.csv`: the 2,316 Archive records in the gen2 table that are missing from the gen2 `archive` index, with the field, value and error OpenSearch rejected them on. Regenerated from live data, with a new `orphaned` column and `parent_collection_title` filled in.
- `gen2-orphaned-archives.csv`: the 75 Archive records whose `parent_collection` ID isn't in the gen2 Collection table, with every Archive attribute (73 columns) plus `rejected_by_opensearch`.

## Next steps

1. **Everything in the 2026-09-30 handoff is still open.** `gen2-main` hasn't been pushed, the index templates aren't installed (`GET /_index_template` returns none), and the gen2 `archive` index still has the dynamic mapping with 8,171 of 10,487 documents.
2. **Decide what to do with the orphaned archives.** They reference four collection IDs that don't exist in gen2:

   | Missing `parent_collection` | Archives |
   |---|---|
   | `cebaa240-928c-4c18-93c9-169c1c41ada5` | 69 |
   | `92441424-3977-4c30-a9f8-011743f26ffb` | 3 |
   | `5d9ae214-31a7-49a0-b78b-761d9a8f5e72` | 2 |
   | `this is a string` (test record `3afbef8d-ed06-418b-be72-c61ec2d958fb`) | 1 |

   Not checked: whether those collections exist in the pprd Collection table (which would mean the bulk copy missed them) or are missing there too.
3. **Rebuilding the index won't fix orphans.** After the handoff's `--recreate` and backfill, all 75 will be indexed and searchable, but still point to collections that don't exist.

## State to know about

- **Orphan test:** an archive is orphaned if any ID in its `parent_collection` list is absent from the Collection table. Every archive has a list; all but one have exactly one entry. The archives' `collection` and `heirarchy_path` attributes were not checked.
- **Overlap:** only 3 of the 75 orphans are in the rejected list (`REY_REY_000021`, `REY_REY_000023` and the test record). The other 72 are indexed.
- **Scripts** (in this folder, for regenerating):
  - `rejected.py` diffs the tables against the indexes by scrolling IDs, replays the missing records into a temporary index created from the live mapping, reads the bulk errors, deletes the temporary index and writes the CSV.
  - `orphans.py` writes the orphaned-archives CSV and reads the rejected CSV for its last column, so run it second.
  - Both expect `Archive.json` and `Collection.json` next to them, produced with `aws dynamodb scan --table-name <Model>-b7anxcwcargyxfsgq4vtrtdbem-gentwo --output json`. They need python3, the AWS CLI and curl ≥ 7.75; boto3 isn't installed.
- **Once the index is recreated with the new mapping, `rejected.py` will report nothing missing.** The rejected CSV describes the current dynamic mapping only.
- **CSV conventions:** list values are joined with `; `, nested objects are JSON, booleans are `True`/`False`. `orphaned` is blank for Collection rows (there are none at present).
