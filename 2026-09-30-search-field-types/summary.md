# Session summary: explicit OpenSearch field types (2026-09-30)

Repo: `~/dev/dlp/access/dlp-access-next-cdk`, branch `whunter/search-field-types`. Also touched `~/dev/dlp/aws/opensearch/*.json` (not in git) and two items in the pre-production Amplify Collection table.

## Goal

Stop relying on OpenSearch dynamic mapping for the `archive` and `collection` indices: bring the hand-maintained mapping files in line with the GraphQL schema, install them through the CDK stack, and make search sorting work on date fields.

## What happened

### 1. Comparing the mapping files with the schema
- Diffed top-level keys in `~/dev/dlp/aws/opensearch/archive-mappings.json` against `Archive`/`Collection`, and `collection-mappings.json` against `Collection`.
- Removed fields not in the schema: `__typename`, `belongs_to`, `circa`, `createdAt`, `related_url`, `resource_type`, `rights_statement`, `updatedAt` (archive); `__typename`, `circa`, `date` (collection).
- Added `alt_text`, `extracted_text`, `taxonomy`, `visual_description` to the archive mapping. The three AWSJSON fields hold plain strings in the vtdlpdev/vtdlppprd tables, so they were mapped as text + keyword, not `object` (which would reject them).
- Located the Gen 2 schema for reference: `~/dev/dlp/access/dlp-access/amplify/data/resource.ts` (SDL string at line 10, `defineData` at 592, VTL overrides in `amplify/data/resolvers/`).

### 2. Installing the mappings from CDK (`d3d088d`)
- Copied the files to `infra/schema/opensearch/{archive,collection}.json`.
- `data-stack.ts` now creates one index-template custom resource per searchable model, passing the mappings as a JSON string (CloudFormation stringifies numbers/booleans in custom resource properties).
- `lambda/opensearch-index-template/index.py` PUTs `dlpnext-<index>` with the mappings, `auto_expand_replicas: 0-1` and priority 1, and now DELETEs the template on Delete (404 ignored), which also cleans up the old `dlpnext-defaults`.
- Tests: Jest checks each template's mappings and that every mapped field exists on the schema type; new pytest `tests/test_index.py` covers the handler.

### 3. Trimming, then completing the mappings (`dc04a21`, `70c26d5`, `d32524d`)
- The user first removed `archived`, `explicit` and `visibility`, then decided every schema field should be mapped.
- Added all missing stored fields with schema types: String/ID → text + keyword, Boolean → boolean, AWSJSON → `object` with no nested properties (`collectionOptions` is stored as a DynamoDB map). Relationship fields (`partner`, `archives`) left out.

### 4. Sorting on date and boolean fields (`4fe93dd`, `d32524d`)
- The resolvers had sorted on `<field>.keyword` except for a hardcoded `visibility`/`start_date`, so other date fields failed.
- New `lib/search-mappings.ts` (`searchMappings`, `numericSortFields`) derives the date and boolean fields from the mappings; `openSearchQueryCode` sorts those on the field itself.
- Page tokens for those fields are returned as strings and converted back with `Number()` for `search_after`. Missing values sort last at `±Number.MAX_SAFE_INTEGER` instead of OpenSearch's ±2^63, which a JS number can't represent exactly.
- New `test/resolvers.test.ts` executes the generated APPSYNC_JS code in Node with a stubbed `util`.

### 5. Embargo dates as dates (`53ed51a`)
- `embargo_start_date`/`embargo_end_date` changed to `AWSDateTime` on `CatalogItem`, `Archive` and `Collection` (the user chose this over changing only the mappings; the interface forces all three to match).
- Both mappings map them as `date`, with `strict_date_optional_time` appended to the format, because the stored values are ISO timestamps that the old format rejected.

### 6. Data fix in pre-production
- Removed `embargo_start_date` and `embargo_end_date` (both `""`) from Collections `a3b1ddc8-b69b-493d-b4d4-ace8e61e7857` and `e6e3597c-4299-4fd3-8500-5debf0721ebb` ("Sample and Test Collection") in `Collection-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd`, conditional on the values still being `""`. A rescan found no empty embargo dates left.

## Files changed (dlp-access-next-cdk)
- `infra/schema/opensearch/archive.json`, `collection.json` (new)
- `infra/schema/schema.graphql` (embargo dates → `AWSDateTime`)
- `infra/lib/search-mappings.ts` (new), `data-stack.ts`, `api-stack.ts`, `resolvers.ts`
- `infra/lambda/opensearch-index-template/index.py`, `tests/test_index.py` (new)
- `infra/test/app.test.ts`, `infra/test/resolvers.test.ts` (new)
- `CLAUDE.md` (index template and sorting notes)

## Verification
- `npx tsc --noEmit` clean; `npm test` 77 passing; `npm run test:lambda` 10 passing; dev Api stack synthesizes. Not deployed.
