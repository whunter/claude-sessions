# Hand-off: collection metadata inventory

## State

- This session only read data. No code repo was changed, and nothing was written to AWS.
- The three output files were on `~/Desktop` and are now in this directory. See `session-summary.md` for what each one contains.
- The CSVs show live vtdlppprd data as of 2026-11-19. Running the DynamoDB scan again will pick up any newer collections.

## Next steps

1. **Review the template with collection managers.** The 7 item-only headers have been removed, which leaves 25 headers that no collection uses yet. `alt_text` (for the thumbnail) and `other_identifier` were kept on purpose. They were removed from the crosswalk too.
2. **Decide what to do about fields the API doesn't return.** `rights_statement`, `date`, `type`, `extent`, `format`, `repository`, `related_url` and `tags` already have data in vtdlppprd. The `Collection` type in `dlp-access-next-cdk/infra/schema/schema.graphql` doesn't include them, so the site can't show them. The fix is either to add them to the schema, or to stop the ingest from accepting them for collections.
3. **Ask about the undocumented headers:** `belongs_to`, `circa`, `provider` and `resource_type`. Their DC mappings in the crosswalk are guesses based on the names.
4. **Possible ingest clean-ups in `dlp-ingest`:**
   - Save `explicit` as `explicit_content`.
   - Write `create_date` and `modified_date` in ISO 8601.
   - Reject the item-only headers on collection CSVs, or warn when they're used.
5. **Clean up the duplicate attributes** (`createdat`, `updatedat`, `_typename`) if they really are leftovers.

## Commands to regenerate

```sh
aws dynamodb scan --table-name Collection-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd --output json > coll.json
```

Then sort the items by `createdAt` (newest first), take the first 5, and write the CSV. The scan returns all 67 records in one response; the CLI follows pagination automatically.
