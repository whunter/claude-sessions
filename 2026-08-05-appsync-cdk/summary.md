# Session: AppSync CDK stack for dlp-access-next

**Date:** 2026-08-05
**Repo:** `dlp-access-next-cdk` (branch `whunter/appsync`)
**Goal:** Give the Next.js app (deployed on Elastic Beanstalk) a way to query the existing `vtdlp` GraphQL data via AppSync, using IAM authorization, defined as a CDK stack.

## Starting point

- User pointed to the [AWS CDK `aws_appsync` Python docs](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_appsync/README.html) and asked for a CDK script to deploy an AppSync instance based on the schema at `dlp-access/amplify/backend/api/vtdlp/schema.graphql`, queryable from the EB-hosted Next.js app via IAM auth.
- `dlp-access-next-cdk` had no existing CDK code — despite the repo name, it was a plain Next.js app (package.json, next.config.ts, Dockerfile, src/app).

## Key discovery: the schema isn't plain AppSync SDL

The source schema uses **Amplify GraphQL Transformer** directives (`@model`, `@searchable`, `@auth` with Cognito groups, `@hasOne`/`@hasMany`, `@index`) that plain CDK `aws_appsync` constructs don't understand. This forced a design decision before any code could be written.

## Clarifying questions asked (and answers)

| Question | Answer |
|---|---|
| How to handle Amplify-only directives? | **Hand-rolled schema + resolvers** (not the Amplify GraphQL API L3 construct) |
| Auth scope? | **IAM only** — no Cognito groups/public auth preserved; authorization enforced app-side |
| CDK language? | **TypeScript** (matches this repo's existing npm/Next.js stack, not Python) |
| Reuse existing resources or build fresh? | **Reuse existing Amplify-provisioned DynamoDB tables** rather than creating new ones |
| CRUD/subscriptions needed? | **Read-only** (get/list/indexed-lookups + relation fields only) |
| Which environment's tables? | **`vtdlpdev` only for now**, parameterized for prod later |

## Investigation before writing code

Used AWS CLI (already authenticated as `vtdlp-whunter-workload`, account `226388486048`) to ground the design in real, live infrastructure rather than guesses:

- Read `amplify/backend/amplify-meta.json` and `team-provider-info.json` in the sibling `dlp-access` repo to find the deployed AppSync API ID (`bxbkjhe235e3jcwcjcji5txvlm`) and confirm the `vtdlpdev` environment.
- `aws dynamodb list-tables` + `describe-table` for all 8 `@model` types (Archive, Collection, Collectionmap, History, MetadataField, PageContent, Partner, Site) to get real partition keys and GSI names (e.g. `Identifier` GSI on `identifier`, `SiteId` GSI on `siteId`, `gsi-Collection.archives` on `collectionArchivesId`).
- Read the **actual deployed VTL resolver templates** (`amplify/backend/api/vtdlp/build/resolvers/*.vtl`) to reverse-engineer the exact foreign-key attribute names Amplify uses for relations that aren't obvious from the schema alone: `archiveCollectionId`, `archivePartnerId`, `collectionArchivesId`, `collectionCollectionmapId`, `collectionPartnerId`, `collectionmapCollectionId`, `pageContentPageContentSiteIdId`.
- `aws elasticbeanstalk describe-applications` / `describe-configuration-settings` on the `dlp-access-next` EB app + `dev-env-sc` saved config to find the **real** EC2 instance profile role name used by PR-preview environments: `aws-elasticbeanstalk-ec2-role` (confirmed via `aws iam get-role`).

This grounding avoided guessing table names, key schemas, or the EB role — everything referenced in the CDK stack is a real, currently-live AWS resource.

## What was built

New `infra/` directory in `dlp-access-next-cdk`, a self-contained TypeScript CDK v2 app:

```
infra/
  package.json / tsconfig.json / cdk.json / .gitignore
  bin/appsync.ts          # entry point, account/region + context params
  lib/appsync-stack.ts    # the stack
  lib/resolvers.ts        # APPSYNC_JS resolver-code generators
  schema/schema.graphql   # hand-stripped, read-only SDL
```

**Stack (`AppSyncStack`):**
- New `GraphqlApi` (`dlp-access-next-vtdlp`), `AuthorizationType.IAM` only.
- Imports the 8 existing `vtdlpdev` DynamoDB tables via `Table.fromTableName` (suffix parameterized via CDK context `tableSuffix`, defaulting to `bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev`).
- 27 APPSYNC_JS unit resolvers, generated from 5 reusable templates in `resolvers.ts` rather than hand-writing near-duplicate files:
  - `getByIdCode()` — `Query.getX` → GetItem by `id`
  - `listScanCode()` — `Query.listXs` → Scan with limit/nextToken
  - `queryByIndexCode()` — `archiveByIdentifier`, `collectionByIdentifier`, `partnerByIdentifier`, `siteBySiteId` → Query on the relevant GSI
  - `hasOneCode()` — single-item relations (`Archive.collection`, `Archive.partner`, `Collection.collectionmap`, `Collection.partner`, `Collectionmap.collection`, `PageContent.pageContentSiteId`) → GetItem via a foreign-key attribute on `ctx.source`, with `runtime.earlyReturn(null)` when the FK is absent
  - `hasManyCode()` — `Collection.archives` → Query on `gsi-Collection.archives`
- Grants `appsync:GraphQL` (scoped to this API, all types/fields) to the real `aws-elasticbeanstalk-ec2-role` via `iam.Role.fromRoleName` + `api.grant(...)`.
- `CfnOutput`s for API ID, GraphQL URL, and API ARN.

**Explicitly out of scope** (per the read-only decision):
- No mutations or subscriptions.
- No full-text search (`searchObjects`, `fulltextArchives`, `fulltextCollections` are OpenSearch-backed in the original and weren't ported).
- No `filter` arguments on list queries — only `limit`/`nextToken` pagination.

## Verification

- `npx tsc --noEmit` — clean.
- `npx cdk synth` — succeeded; confirmed in the synthesized template:
  - `AWS::AppSync::GraphQLApi` has `AuthenticationType: AWS_IAM`.
  - 8 `AWS::AppSync::DataSource`, 27 `AWS::AppSync::Resolver` (matches the plan exactly).
  - `EbInstanceRolePolicy` is attached to `Roles: ["aws-elasticbeanstalk-ec2-role"]` with `Action: appsync:GraphQL`, `Resource: arn:aws:appsync:us-east-1:226388486048:apis/<apiId>/*`.
- Removed the `cdk.out/` synth artifacts afterward (not meant to be committed); added `infra/.gitignore`.

## Deploy instructions given to user

```
cd infra
npm install
npx cdk deploy
```

Defaults to account `226388486048` / region `us-east-1`, `vtdlpdev` tables. Override with `-c tableSuffix=...` for a future prod deployment (prod tables use suffix `77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd`, discovered during investigation but not wired up per the "dev only for now" answer).

## State at end of session

- `infra/` is untracked (not yet committed) on branch `whunter/appsync`.
- No `git commit` was made — the user hadn't asked for one.
