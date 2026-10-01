# Handoff: OpenSearch record-count discrepancy (dlp-access Gen 2)

Repo: `~/dev/dlp/access/dlp-access`, branch `gen2-main`. Two commits, `ec3eddf` and `c03fac5`, **not pushed**. Nothing has been deployed, and no live index has been changed.

## Next steps

1. **Push `gen2-main`.** The Amplify build deploys the new `OpenSearchIndexTemplates` custom resource in `SearchableStack`, which installs the `archive-schema`, `collection-schema` and `partner-schema` index templates on the gen2 domain.
2. **Rebuild the gen2 indexes.** Templates only apply when an index is created, so the existing `archive`/`collection` indexes keep their dynamic mappings until they're recreated. Search is empty until the backfill finishes (about a minute).
   ```
   npx tsx scripts/opensearch-mappings.ts apply search-dguapwk5zhfbjhfosoj4a7n4uri-h6h32vch36iuywtzs7u2zxyjji.us-east-1.es.amazonaws.com --recreate
   node scripts/backfill-opensearch.js Archive-b7anxcwcargyxfsgq4vtrtdbem-gentwo Collection-b7anxcwcargyxfsgq4vtrtdbem-gentwo
   ```
   Set `STREAMING_FUNCTION_NAME` if the backfill reports more than one Lambda mapped to a table's stream.
3. **Verify.** `searchObjects(limit:0){ total }` should report ≥10,000 (the cap) on gen2. Directly on the domain, `GET /archive/_count` should be 10,487 and `GET /collection/_count` 68.
4. **pprd (optional).** That domain isn't deployed from this backend, so install the templates with the script: `apply search-amplify-opense-1mgsd2s4iujlk-l6dv6pdqzzmi32tc5bdv65iynq.us-east-1.es.amazonaws.com --recreate`, then backfill the `-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd` tables. Check first which streaming Lambda feeds that domain.
5. **Data cleanup (optional).** `gen2-opensearch-rejected-records.csv` in this folder lists the 2,316 archives rejected today, with the field and value OpenSearch failed on. Notable bad values:
   - 162 archives have `start_date: 7999/10/10` and `end_date: 999/10/10`.
   - 1 archive has `this is a string` in both fields.
   - Some `parent_collection` IDs aren't in the Collection table.

## State to know about

- **Domains:** gen2 is `dguapwk5zhfbjhfosoj4a7n4uri` (AppSync `i5bb5onvknesbdxzscz6waegly`). pprd is `amplify-opense-1mgsd2s4iujlk` (AppSync `ine23khrhnbybivaus6gixlfci`). Both are Elasticsearch 7.10. The user's IAM user can't call `appsync:ListDataSources`; the domains were identified by their doc counts.
- **Source of truth:** `amplify/data/opensearch-mappings.ts` builds the mappings from the SDL string in `resource.ts`.
  - String/ID map to text + `.keyword`. Boolean maps to `boolean`, and `createdAt`/`updatedAt` to `date`.
  - AWSJSON maps to `object` with `enabled: false`, so it's kept in `_source` but not indexed.
  - The root has `"dynamic": false`, so attributes not in the schema aren't indexed.
- **Date fields** (`DATE_FIELDS`): `date`, `start_date`, `end_date`, `embargo_start_date`, `embargo_end_date`.
  - **GraphQL:** they stay `String`. The user chose this after seeing that only 81 of 7,582 archive `start_date` values are valid `AWSDate`, which would break AppSync reads.
  - **OpenSearch:** they're `date` with the formats from `~/dev/dlp/aws/opensearch/archive-mappings.json.bak`, plus `ignore_malformed: true`. An unparseable value is left out of that field, and the document is still indexed.
  - **`display_date`** stays free text.
- **Values still skipped under the new mapping** (gen2 tables): archive `date` 1,397, `end_date` 163, `start_date` 1; collection `start_date` 2, embargo dates 3 each. The embargo values are ISO timestamps with milliseconds (`2025-12-04T06:00:00.010Z`), which the `.bak` formats don't include. Adding `strict_date_optional_time` to `DATE_FORMATS` would accept them; the dlp-access-next-cdk session (2026-09-30-search-field-types) did that.
- **Resolvers:** `nonKeywordFields` is now `["visibility", "start_date", "end_date"]` in all five `*.req.vtl`, because date fields have no `.keyword` subfield.
- **Custom resource handler** (`amplify/data/opensearch-index-templates/index.mjs`) has no dependencies and signs its requests itself. Its signing was tested with read-only GETs against the gen2 domain. Delete ignores errors, so a stack teardown can't hang on it.
- **`graphql`** is used by `opensearch-mappings.ts` but isn't a direct dependency; it comes in through the Amplify packages (v15.10.3).
- **`scripts/backfill-opensearch.js`** can't detect per-document rejections. The streaming Lambda swallows them, and the script only inspects the invoke log tail. Running `opensearch-mappings.ts validate` against the tables beforehand is the reliable check.
