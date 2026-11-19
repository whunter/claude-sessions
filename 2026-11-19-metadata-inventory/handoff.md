# Hand-off: collection metadata inventory

## State

- This session only read data. No code repo was changed, and nothing was written to AWS.
- The three output files were on `~/Desktop` and are now in this directory. See `session-summary.md` for what each one contains.
- The CSVs show live vtdlppprd data as of 2026-11-19. Running the DynamoDB scan again will pick up any newer collections.

## Next steps

1. **Review the template with collection managers.** The template now has only fields from the `Collection` type in the old Amplify schema or the CDK schema: 33 columns. 28 headers the ingest accepts were removed from the template and the crosswalk because neither schema has them. 8 of those already hold data in vtdlppprd (see step 2). `ownerinfo` was added as `ownerinfo_name` and `ownerinfo_email`, the same split the old admin form uses. The ingest doesn't read those two columns yet. `partner_id` was left out as a system field (the key to the Partner record).
2. **Decide what to do with collection data that isn't in the schema.** These headers were dropped from the template, but vtdlppprd records already hold values for them, and neither schema returns them: `date` (12 records), `tags` (6), `rights_statement` (5), `extent` (5), `type` (4), `repository` (4), `format` (3) and `related_url` (1). The ingest still accepts them, and 20 more headers, for collections. Choose whether to add any of them to the schema, or to stop the ingest accepting them and clean up the stored values.
   - `provider` is in the Amplify schema but not the CDK one, so the new site can't read it yet.
3. **Ask about `provider`.** The site's field reference doesn't document it, so its DC mapping in the crosswalk is a guess based on the name.
4. **Possible ingest clean-ups in `dlp-ingest`:**
   - Save `explicit` as `explicit_content`.
   - Read `ownerinfo_name` and `ownerinfo_email` into the `ownerinfo` JSON field.
   - Write `create_date` and `modified_date` in ISO 8601.
   - Reject headers that aren't in the `Collection` schema on collection CSVs, or warn when they're used.
5. **Clean up the duplicate attributes** (`createdat`, `updatedat`, `_typename`) if they really are leftovers.

## Commands to regenerate

```sh
aws dynamodb scan --table-name Collection-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd --output json > coll.json
```

Then sort the items by `createdAt` (newest first), take the first 5, and write the CSV. The scan returns all 67 records in one response; the CLI follows pagination automatically.
