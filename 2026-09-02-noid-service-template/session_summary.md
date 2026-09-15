# Session Summary — noid-service-template

**Date:** 2026-09-02

## Task

Refactor `aws/cloudFormation/vtdlp-noid-services/20260902_mint_service.template` so its
Lambda functions are granted DynamoDB permissions on a specified, *existing* table —
mirroring how `20260902_resolution_service.template` grants permissions — instead of
creating its own table and using SAM's `DynamoDBCrudPolicy` shorthand tied to that
created table.

## Background

- `20260902_resolution_service.template`: creates a Lambda + IAM Role with an explicit
  inline policy statement granting DynamoDB CRUD-style actions on a table named via the
  `TargetTableName` parameter (no table resource in the template — the table is assumed
  to already exist).
- `20260902_mint_service.template` (before this session): a SAM template that created its
  own `ResolutionTable` DynamoDB table (via `NSTableName` parameter) and granted its two
  Lambdas (`NoidFunction`, `UpdateFunction`) permissions on that table using the SAM
  `DynamoDBCrudPolicy` policy template.

Clarified with the user which refactor was intended: drop the table creation entirely and
point the mint service at an existing table (parameter-driven), matching resolution
service's approach — rather than keeping table creation and just swapping the policy
mechanism.

## Changes made

In `20260902_mint_service.template`:

1. Removed the `ResolutionTable` `AWS::DynamoDB::Table` resource — the template no longer
   provisions a table.
2. Replaced the `NSTableName` parameter (`Default: mint`) with `TargetTableName` (no
   default), matching resolution_service's naming/shape for an existing-table parameter.
3. Replaced `Policies: [DynamoDBCrudPolicy: {TableName: Ref: NSTableName}]` on both
   `NoidFunction` and `UpdateFunction` with an explicit IAM policy statement (raw SAM
   policy document form: `Version` + `Statement`), granting the same 9 actions
   `DynamoDBCrudPolicy` originally granted:
   `GetItem, DeleteItem, PutItem, Scan, Query, UpdateItem, BatchWriteItem, BatchGetItem,
   DescribeTable`
   on both the table ARN and its `/index/*` ARN, built via `Fn::Sub` referencing
   `TargetTableName` — same construction style used in resolution_service's IAM role
   policy.
   - Note: an earlier draft of this edit added `dynamodb:ConditionCheckItem` (copied
     from resolution_service's action list) but the user corrected this — the action
     list should stay identical to what `DynamoDBCrudPolicy` originally granted (no
     `ConditionCheckItem`). This was fixed in both statements.
4. Updated all other `NSTableName` references (the `MintApi` API name `Fn::Join`, and the
   `NSTable` environment variable on both functions) to `TargetTableName`.
5. Verified no `NSTableName` references remain in the file.

## Result

`20260902_mint_service.template` now takes `TargetTableName` as a parameter for an
already-existing DynamoDB table (no table resource created by this stack) and grants
`NoidFunction`/`UpdateFunction` explicit IAM permissions on it, structurally consistent
with `20260902_resolution_service.template`.

No commits were made — only the template file was edited in place.
