# Session: AppSync query examples page in dlp-access-next-cdk

**Date:** 2026-08-05
**Repo:** `dlp-access-next-cdk` (branch `whunter/appsync`)
**Goal:** Add a route, `examples/appsync-queries`, whose page demonstrates querying the AppSync API on load — running every query in `infra/schema/schema.graphql` and rendering each result with a label.

## Starting point

- Continuation of the same branch as the earlier `2026-08-05-appsync-cdk.md` session, which built the `infra/` CDK stack (`DlpAccessNextAppSyncStack`) exposing AppSync with **IAM-only** authorization.
- The Next.js app itself (`src/app`) had zero AppSync/AWS SDK integration before this session — no client, no env var wiring, no example usage anywhere in `src`.

## Key constraint: IAM auth means server-side only

The CDK stack authorizes the API with `AuthorizationType.IAM` and grants `appsync:GraphQL` to the Elastic Beanstalk EC2 instance role — there's no Cognito Identity Pool for browser-side credentials. That ruled out a client-side fetch and pointed to an async **Server Component** that signs and runs the queries at request time (satisfies "on page load" without ever exposing AWS credentials to the browser).

## What was built

- **`src/lib/appsync.ts`** — server-only signed GraphQL client:
  - `aws4fetch`'s `AwsClient` for lightweight SigV4 request signing.
  - `@aws-sdk/credential-provider-node`'s `defaultProvider()` for credential resolution — works locally via `~/.aws` credentials/env vars, and via the EB instance role in production, matching the CDK grant.
  - Reads `APPSYNC_API_URL` (required) and `AWS_REGION` (default `us-east-1`) from env; throws a clear error if the URL isn't configured.
  - `graphqlRequest<T>(query, variables)` posts signed requests and surfaces both HTTP and GraphQL `errors[]` failures as thrown `Error`s.

- **`src/app/examples/appsync-queries/queries.ts`** — orchestrates all 9 queries declared in `schema.graphql`:
  - The three no-arg queries (`listArchives`, `listCollections`, `listSites`) run first, in parallel.
  - Their first returned item seeds the `id`/`identifier`/`siteId` arguments for the six queries that require them (`getArchive`, `archiveByIdentifier`, `getCollection`, `collectionByIdentifier`, `getSite`, `siteBySiteId`), so the whole schema gets exercised without any hardcoded IDs.
  - Each query is wrapped individually (`run`/`skip` helpers) so one failure or an empty list doesn't take down the rest of the page — each result carries a `status` of `success` / `error` / `skipped`.
  - Results are returned in the same order the `Query` type declares them in `schema.graphql`.

- **`src/app/examples/appsync-queries/QueryResultCard.tsx`** — presentational card: query label, a color-coded status badge, a one-line description of what was run (including which seed value was used), and either pretty-printed JSON or the error/skip reason.

- **`src/app/examples/appsync-queries/page.tsx`** — the route itself (`export const dynamic = "force-dynamic"` so it always re-runs server-side per request rather than being statically cached). Shows a setup-instructions panel instead of attempting the fetch when `APPSYNC_API_URL` isn't configured.

- Added dependencies to the app's `package.json`: `aws4fetch`, `@aws-sdk/credential-provider-node` (the first AWS SDK deps in the Next.js app itself — CDK's own deps in `infra/` are separate).

## Verification

- `npx tsc --noEmit` — clean.
- `npm run lint` — clean for all new/changed files (pre-existing errors only in the generated `infra/cdk.out/` bundle, unrelated).
- `npm run build` — succeeded; route registered as `ƒ /examples/appsync-queries` (dynamic/server-rendered), as intended.
- `npm run start` + `curl` against the running server confirmed the unconfigured-environment fallback renders correctly (no `APPSYNC_API_URL` is set in this environment, so the amber setup notice shows rather than 9 duplicate connection errors).
- Noted, but did not touch, pre-existing high-severity `npm audit` findings in `next`/`postcss`/`sharp` — unrelated to this change and out of scope.

## State at end of session

- `src/app/examples/` and `src/lib/` are new, untracked files on branch `whunter/appsync`.
- `package.json` / `package-lock.json` modified (new deps).
- No `git commit` was made — the user hadn't asked for one.
- Not yet deployed/tested against a live AppSync endpoint — `APPSYNC_API_URL` still needs to be set from the `GraphQLApiUrl` CDK output once the stack in the prior session is deployed.
