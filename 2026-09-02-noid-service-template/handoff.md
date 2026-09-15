# Hand-off — noid-service-template

## Current state

`aws/cloudFormation/vtdlp-noid-services/20260902_mint_service.template` has been edited
(uncommitted — this directory is not a git repo per the environment info, so there's no
git state to worry about, but confirm the file's location isn't itself under a repo
elsewhere before treating it as "safe").

Key structural change: the template **no longer creates a DynamoDB table**. It now
expects an existing table name via the `TargetTableName` parameter and grants
`NoidFunction`/`UpdateFunction` explicit IAM DynamoDB permissions on it (GetItem,
DeleteItem, PutItem, Scan, Query, UpdateItem, BatchWriteItem, BatchGetItem,
DescribeTable — matching what `DynamoDBCrudPolicy` used to grant).

## Things to double check / possible follow-ups

1. **Deployment parameter update needed.** Anyone deploying this stack must now pass
   `TargetTableName` (an existing table) instead of `NSTableName`. If there's a
   deploy script, Makefile, CI config, or SAM `samconfig.toml`/parameter-overrides file
   referencing `NSTableName`, it needs updating too — this session did not search for
   or touch deployment tooling outside the template file itself.
2. **Table must already exist / be created elsewhere.** Since mint_service no longer
   creates the table, something else (manually, or another CFN stack) needs to create a
   table with the same schema mint_service previously created inline:
   - Partition key: `short_id` (S)
   - GSI `long_url-index` on `long_url` (S), full projection
   - Billing mode: PAY_PER_REQUEST
   If resolution_service's `TargetTableName` is meant to point at this same table, verify
   the schema resolution_service expects lines up with what mint_service used to create.
3. Only `20260902_mint_service.template` was touched. `20260902_resolution_service.template`
   was read for reference but not modified.
4. No validation was run against a real `aws cloudformation validate-template` / `sam
   validate` — only manual inspection (no PyYAML available in this environment to
   lint the YAML). Worth running `sam validate` or `aws cloudformation validate-template`
   before deploying.

## Not done

- No commit was made.
- No changes to any other files/services.
