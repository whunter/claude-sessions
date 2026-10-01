# Session summary: gen2 rejected-records and orphaned-archives CSVs (2026-10-01)

Started from `~/dev/dlp/access/dlp-access` (branch `gen2-main`), which was not changed. Read, without changing, the gen2 OpenSearch domain and DynamoDB tables. Outputs were written to `~/dev/dlp/claude-sessions/2026-09-30-item-inspection/`.

## Goal

Re-create the CSV of gen2 records rejected by OpenSearch, with causes, from the 2026-09-30 "item-inspection" handoff, and add a column showing whether an Archive is orphaned because its Collection doesn't exist. Then list all orphaned archives in a separate CSV with every field.

## What happened

### 1. Checking the current state
- Read the 2026-09-30 handoff and summary. The CSV from that session was still in the folder; it was regenerated from live data, not edited.
- The gen2 domain was unchanged since that session: no index templates, `archive` still dynamically mapped with `display_date`, `date`, `created`, `create_date`, `modified_date`, `start_date` and `end_date` as `date` fields, 8,171 archive documents and 68 collection documents.

### 2. Rejected-records CSV
- Scanned both gen2 tables: 10,487 archives, 68 collections.
- Scrolled the IDs of both indexes and compared: 2,316 archives missing, no collections missing, nothing in the index that isn't in the table.
- Replayed the 2,316 into a temporary index created from the live `archive` mapping. All were rejected with `mapper_parsing_exception`. The temporary index was deleted.
- First failing field per record: `display_date` 2,112, `end_date` 166, `start_date` 28, `create_date` 6, `date` 3, `created` 1. These match the 2026-09-30 counts.
- Added `orphaned` (`True` when a `parent_collection` ID isn't in the Collection table): 3 of the 2,316. Two Reynolds records point to `92441424-3977-4c30-a9f8-011743f26ffb`; the test record has `this is a string`.
- `parent_collection_title`, blank in the earlier file, is now filled from the Collection table.

### 3. Orphaned-archives CSV
- Across the whole Archive table, 75 archives reference a collection that doesn't exist: 69 to `cebaa240-928c-4c18-93c9-169c1c41ada5`, 3 to `92441424-3977-4c30-a9f8-011743f26ffb`, 2 to `5d9ae214-31a7-49a0-b78b-761d9a8f5e72`, and the test record.
- Wrote them to `gen2-orphaned-archives.csv` with all 73 attributes found in the Archive table, plus `rejected_by_opensearch` (`True` for 3). Ten columns are empty for these rows and were kept so the layout matches the table.
- This file used the table scan from step 2, taken earlier in the same session.

## Files

In `2026-09-30-item-inspection/`:
- `gen2-opensearch-rejected-records.csv` (regenerated; commit `e22f5a5`)
- `gen2-orphaned-archives.csv` (new; commit `2703a48`)

In this folder:
- `rejected.py`, `orphans.py`: the scripts that produced the two files.
