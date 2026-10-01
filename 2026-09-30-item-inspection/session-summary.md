# Session summary: OpenSearch record-count discrepancy (2026-09-30)

Repo: `~/dev/dlp/access/dlp-access`, branch `gen2-main`. Commits `ec3eddf`, `c03fac5` (not pushed). Also read, without changing, the gen2 and pprd OpenSearch domains and DynamoDB tables.

## Goal

The gen2 site (`gen2-main.d1n265krqy0ld3.amplifyapp.com`) and the pprd site (`federated-pprd.dlp.cloud.lib.vt.edu`) have the same Archive and Collection records, copied in bulk, but report different search counts. Find out why, and make the OpenSearch mappings match the GraphQL schema.

## What happened

### 1. Measuring the gap through AppSync
- Took each site's AppSync endpoint and API key from its JS bundle and queried `searchObjects` directly. gen2 reported 8,239 and pprd 10,000. 10,000 is OpenSearch's default `track_total_hits` cap.
- Paged through every document on both sides. Collections matched (68). pprd had 2,153 more archives, and every gen2 document was also on pprd.
- `getArchive` (which reads DynamoDB) found the extra records in gen2's table too, so **gen2's index was missing documents**; pprd's didn't have stale ones.

### 2. Finding the cause
- The missing documents didn't cluster by collection or date. Comparing field shapes showed they had free-text `display_date` values ("September 29, 1862", "approx. 1870"), while the indexed ones had ISO dates.
- A rule based on date formats (`display_date` must be ISO; `start_date`/`end_date`/`date`/`create_date`/`modified_date` must be `yyyy/MM/dd`) predicted all 2,153 missing documents with no false positives.
- With AWS credentials, the live mappings confirmed it. Both indexes are dynamically mapped with no templates. On gen2, date detection had made `display_date`, `date`, `created`, `create_date`, `modified_date`, `start_date` and `end_date` into `date` fields. pprd's mapping is more lenient: `start_date`/`end_date` accept the `.bak` formats, and the others are text.
- **Root cause:** dynamic mapping guessed date types from the first documents the backfill indexed. Every later document with an unparseable value was rejected, and the streaming Lambda swallowed the error.
- DynamoDB has 10,487 archives in both environments, so pprd was also missing 163.

### 3. Schema-derived mappings (`ec3eddf`, `c03fac5`)
- The first version (`scripts/opensearch-mappings.js`) mapped every String as text + keyword and `start_date` as keyword. In a temporary index, all 10,487 archives were indexed with that mapping.
- The user asked for `date`, `start_date`, `end_date`, `embargo_start_date` and `embargo_end_date` to become `AWSDate` in the schema. A scan showed most stored values aren't valid `AWSDate` (81 of 7,582 archive `start_date`), so AppSync reads would fail. The user chose to keep them `String` in GraphQL and map them as dates in OpenSearch only, using the `.bak` formats plus `ignore_malformed`.
- Moved the mapping builder to `amplify/data/opensearch-mappings.ts`. `resource.ts` now adds a Lambda-backed custom resource in `SearchableStack` that installs index templates on deploy; its IAM access is limited to `_index_template/*`. Checked with `tsc` and a local `cdk synth`.
- The script became `scripts/opensearch-mappings.ts` (run with `npx tsx`): `print`, `validate` (temporary index; reports rejections and skipped date values), and `apply [--recreate]`.
- Added `end_date` to `nonKeywordFields` in the five search resolvers.
- Validation against the gen2 tables: 10,487 archives and 68 collections, **0 rejected**.

### 4. What pprd does with the same data
- pprd's `archive` index maps `start_date`/`end_date` with the `.bak` formats. `date` and the embargo fields are text there. Its `collection` index has `end_date` with only `yyyy/MM/dd` formats and the embargo fields as ISO dates. Nothing uses `ignore_malformed`.
- pprd tables: 10,487 archives, 10,324 indexed. The 163 missing are exactly the records with unparseable `start_date`/`end_date`: 162 with `7999/10/10`/`999/10/10` and 1 with `this is a string`. Indexing them into a temporary index on pprd reproduced the `mapper_parsing_exception`. The 1,397 unparseable `date` values are indexed on pprd because the field is text there.

### 5. List of rejected gen2 records
- Compared the gen2 tables with the gen2 index (scroll): 2,316 archives missing, no collections.
- Replayed all 2,316 into a temporary copy of gen2's live mapping, and all were rejected (`mapper_parsing_exception`). The first failing field: `display_date` 2,112, `end_date` 166, `start_date` 28, `create_date` 6, `date` 3, `created` 1.
- Written to `gen2-opensearch-rejected-records.csv` in this folder.

## Files changed (dlp-access)

- `amplify/data/opensearch-mappings.ts` (new): mapping builder and `DATE_FIELDS`.
- `amplify/data/opensearch-index-templates/index.mjs` (new): custom resource handler.
- `amplify/data/resource.ts`: `addOpenSearchIndexTemplates()`.
- `amplify/data/resolvers/*.req.vtl` (5): `end_date` added to `nonKeywordFields`.
- `scripts/opensearch-mappings.ts` (new): print / validate / apply.

All temporary indexes created during the session were deleted. Neither live index was modified.
