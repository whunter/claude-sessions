# Session summary: Gen 2 migration, Step 4 post-generate (2026-09-29)

Repo: `~/dev/dlp/access/dlp-access`, branch `gen2-main`. The Gen 1 env is `gentwo` (app `vtdlp-dev`, us-east-1).

## Goal

Follow the AWS guide from [Step 4: Post-Generate](https://docs.amplify.aws/react/start/migrate-to-gen2/migrate-existing-app/#step-4-post-generate) to prepare the generated Gen 2 backend for deployment.

## Starting point

`amplify gen2-migration generate` had already been run and committed (`7e3db95`, `a1cdc00`, `dd44c35`). It generated `amplify/` (auth, data with 8 models plus VTL resolvers, storage, the S3 trigger function) and `amplify.yml`.

## Changes (commit `4b9f620`, not pushed)

| File | Change | Why |
|---|---|---|
| `amplify/data/resource.ts` | `migratedAmplifyGen1DynamoDbTableMappings[0].branchName`: `'gentwo'` → `'gen2-main'` | Guide step: Hosting reuses the Gen 1 DynamoDB tables instead of creating new ones |
| `amplify/function/S3Triggerf2aaed76/index.js` | `exports.handler = async function` → `export async function handler` | Guide step: ESM (`amplify/package.json` is `"type": "module"`) |
| `amplify/function/S3Triggerf2aaed76/resource.ts` | `runtime: 18` → `22` | Not in the guide. AWS no longer allows creating or updating Node 18 Lambdas |
| `src/index.js` | Imports `./amplify_outputs.json`; feedback API region now `config.data.aws_region` | Guide step. The path differs from the guide (see below). `aws_project_region` doesn't exist in Gen 2 outputs |
| `amplify.yml` | `pipeline-deploy ... --outputs-out-dir src` | CRA's ModuleScopePlugin blocks imports from outside `src/`, so `../amplify_outputs.json` won't build |
| `amplify/tsconfig.json` | Added `"types": ["node"]` | TypeScript 6 defaults `types` to `[]`, so `tsc` failed on `process`, `fs` and `path`. ampx typechecks the backend during deploy |

Verified: `npx tsc --noEmit -p amplify/tsconfig.json` passes. Not done: deploy, and the frontend build.

## Guide steps that didn't apply

- **Public auth directive:** all 8 models (Archive, Collection, Collectionmap, History, MetadataField, PageContent, Partner, Site) already have explicit `@auth`.
- **Secrets:** none.
- **Social sign-in / callback URLs:** no external providers.
- **Kinesis:** none.
- **REST API name:** `feedbackapi` is an external endpoint (`REACT_APP_FEEDBACK_API_ENDPOINT`) configured by hand in `src/index.js`, not an Amplify resource, so it keeps its name.
- `src/lib/storageTools.js` reads the bucket through `Amplify.getConfig()`, so it works with any config file format.
