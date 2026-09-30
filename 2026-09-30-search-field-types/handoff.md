# Handoff: explicit OpenSearch field types (dlp-access-next-cdk)

Repo: `~/dev/dlp/access/dlp-access-next-cdk`, branch `whunter/search-field-types`. Six commits, `d3d088d` through `53ed51a`, **not pushed**. Nothing has been deployed.

## Next steps

1. **Deploy to dev** (user-run; the confirmation needs a terminal):
   ```
   cd infra && npm run deploy -- -c env=dev -c account=$(aws sts get-caller-identity --query Account --output text)
   ```
   This replaces the Data stack's single `IndexTemplate` custom resource with `ArchiveIndexTemplate` and `CollectionIndexTemplate`. CloudFormation creates the new templates (`dlpnext-archive`, `dlpnext-collection`, priority 1), then deletes the old `dlpnext-defaults` (priority 0) through the handler's new Delete path. The Api stack gets the new resolver code and the `AWSDateTime` schema.
2. **Recreate the dev indices.** Index templates only apply when an index is created, so if `archive` and `collection` already exist on `dlpnext-dev`, they keep their dynamic mappings. Delete them and rewrite the rows to re-index (the stream starts at `LATEST`; there is no reindex step in the stack).
3. **Check sorting on a live domain.** Two things are only tested against a stub of AppSync's `util`:
   - OpenSearch accepting a numeric `missing` value (`±9007199254740991`) on a date/boolean sort.
   - OpenSearch accepting a number in `search_after` for a date/boolean field.
   Sort `fulltextArchives` by `end_date` both ways and page past items with no `end_date`.
4. Push the branch and open a PR when ready.

## State to know about

- **Mapping files** live in `infra/schema/opensearch/archive.json` and `collection.json` (top level `{"mappings": {...}}`). Copies are kept identical at `~/dev/dlp/aws/opensearch/archive-mappings.json` and `collection-mappings.json` (not in git). `.bak` files there hold the versions from before this session.
- **Every stored schema field is mapped** (Archive 69, Collection 39 properties). `partner` and `archives` are relationships and deliberately unmapped. A Jest test fails if a mapping has a field that isn't on the matching schema type (it does not check the other direction).
- **AWSJSON fields:** `alt_text`, `extracted_text`, `visual_description` are mapped as text + keyword because the stored values are plain strings. `collectionOptions` and `ownerinfo` are `{ "type": "object" }` with no nested properties. `archiveOptions` and `manifest_file_characterization` keep their explicit nested properties.
- **Embargo dates** are `AWSDateTime` on `CatalogItem`, `Archive` and `Collection` (they must match the interface) and `date` in both mappings. Their format ends in `||strict_date_optional_time` because stored values look like `2025-12-04T06:00:00.010Z`. `start_date` / `end_date` formats do **not** include ISO timestamps.
- **Empty strings in date fields** fail both AppSync (`AWSDateTime`) and OpenSearch (`date`). The two pprd Collections that had `""` embargo dates were fixed (see summary). Any other `""` in `start_date` / `end_date` would still be rejected at index time and land in the streaming failure queue.
- **Sorting:** `openSearchQueryCode` takes `numericSortFields`, which `api-stack.ts` fills from every `date` and `boolean` field in the mappings (`numericSortFields()` in `lib/search-mappings.ts`). Those sort on the field itself; everything else sorts on `.keyword`. Only `visibility`, `start_date` and `end_date` of those are in the schema's sortable-field enums.
- **Pre-existing, not addressed:** paging with `search_after` on a single sort field skips documents with tied values, and a keyword sort whose last hit lacks the field returns a null `nextToken`, ending paging early.
