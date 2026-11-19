# Session summary: collection metadata inventory

- Date: 2026-11-19
- Repos read (none changed): `dlp-ingest`, `dlp-access`, `dlp-access-next-cdk`
- AWS: read-only scan of DynamoDB table `Collection-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd` (67 records)

## Goal

Give collection managers a list of the Collection metadata headers they can fill in, and map each one to Dublin Core.

## Outputs (in this directory)

| File | What it is |
|---|---|
| `vtdlppprd-collection-newest-5.csv` | Raw export of the 5 newest collections, by `createdAt`. It has all 48 attributes found in the table: every attribute any of the 67 records has. Lists and maps are written as JSON. |
| `vtdlppprd-collection-metadata-template.csv` | The same 5 collections cut down to the 66 headers a manager can supply, with multiple values joined by `||` so the file is valid ingest input. Columns 1–34 are the ones the table uses. Columns 35–66 are headers the ingest accepts but no vtdlppprd collection uses; those are empty. |
| `vtdlppprd-collection-dublin-core-crosswalk.md` | Maps each header to its closest `dcterms:` term and rates the match (Exact, Close, Loose or None). For each term it gives DCMI's recommended usage, an illustrative DC example, and a real value from vtdlppprd. When vtdlppprd has no value, it uses the example from the site's field reference instead. It also shows whether the Collection GraphQL type returns each field. |

## How the header list was built

- **Start:** the 48 attributes found across the table.
- **Removed, set by AWS or AppSync:** `createdAt`/`createdat`, `updatedAt`/`updatedat`, `__typename`/`_typename`.
- **Removed, set by the ingest:** `id`, `custom_key`, `heirarchy_path`, `parent_collection`, `thumbnail_path`, `collectionmap_id`. In `dlp-ingest`, these come from `batch_import_collections`, `create_item_in_table` and `set_attribute` in `ingest_classes/metadata/generic_metadata.py`.
- **Removed, not written by the current ingest:** `collectionOptions`. Also `note`, because the ingest saves a CSV `note` column as `embargo_note`.
- **Kept from the form:** `collection_category` (form only; the CSV value is ignored), plus `parent_collection_identifier`, `visibility`, `embargo_start_date` and `embargo_end_date`. A CSV value for these four overrides the form.
- **Added:** every header in `data/headers_keys.json` (single- and multi-value lists), plus `visibility`, `archived` and `filename`, that the table doesn't use yet. That's 32 headers.

## Findings

- **Fields saved but never returned by the API.** The `Collection` GraphQL type doesn't include 8 headers that vtdlppprd already uses: `rights_statement`, `date`, `extent`, `format`, `related_url`, `repository`, `tags` and `type`. It also doesn't include 28 of the 32 headers the ingest accepts but no collection uses. The ingest writes all of these to DynamoDB, but the site can't read them. The old Amplify schema and the CDK schema match here, except `provider`, which only the old schema has.
- **`explicit` is saved under its own name.** The ingest treats it as true/false, the same as `explicit_content`, but saves it as `explicit`, which the Collection type doesn't have.
- **Data quality, compared with DC guidance:**
  - `create_date` and `modified_date` look like record timestamps and use `YYYY/MM/DD`, not ISO 8601.
  - `vtac` lists six creators in one `creator` value.
  - `location` is stored as latitude then longitude, in two values.
  - `source` holds a sentence instead of a URI.
  - `type` describes what the collection contains instead of using the DCMI type `Collection`.
- **Duplicate attribute names.** The table has `createdAt`/`createdat`, `updatedAt`/`updatedat` and `__typename`/`_typename`, probably left over from older imports.

## Method notes

- DC definitions and usage notes were checked against the DCMI Metadata Terms page (2020-01-20). That page cut some notes short, so the rest of those notes come from my knowledge of the spec. The Darwin Core text for `basis_of_record` and `taxonomy` comes from my own knowledge and wasn't checked against the Darwin Core site.
- The DC examples are illustrative. Authority URIs (LCSH, TGN, LC names) were left out instead of guessed, and placeholder links use `example.edu`.
- The access site's field reference doesn't document `belongs_to`, `circa`, `provider` or `resource_type`, so those were mapped from their names.
