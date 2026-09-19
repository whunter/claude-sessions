# Hand-off: AppSync CDK read-only models + OpenSearch search

Repo: `~/dev/dlp/access/dlp-access-next-cdk`, branch `whunter/appsync` (pushed, head `4599c7f`).
Stack `DlpAccessNextAppSyncStack` is deployed to vtdlpdev (us-east-1, acct 226388486048).

## State
- Read-only models: Partner, History, MetadataField, PageContent (Collectionmap skipped). No mutations/subscriptions.
- OpenSearch: `fulltextArchives`, `fulltextCollections`, `searchObjects` (returns `[CatalogItem]`, tagged by `__typename`). Deployed and smoke-tested live.
- Examples page (`src/app/examples/appsync-queries`) demos all queries including the search ones (the search demos are type-checked but not run against the live API).
- Nothing pending.

## Deploy
Run from `infra/`:
`npx cdk deploy -c openSearchDomainEndpoint=search-amplify-opense-2c12c2wf4hmz-5gd4rjsg7uo5nhhuuqlibruz74.us-east-1.es.amazonaws.com`
(the context value is required; deploys are run by the user with `!`, since the auto-mode classifier blocks them).
Dev domain: `amplify-opense-2c12c2wf4hmz`. Prod domain (tag vtdlppprd): `amplify-opense-1mgsd2s4iujlk`.
API ID `76terwujczccni36gntmtys4aq`.

## Gotchas
- AppSync JS runtime forbids reassigning variables (`let x; x = ...`). The deploy fails with the generic "The code contains one or more errors".
- `util.transform.toElasticsearchQueryDSL` returns a JSON string, so wrap it in `JSON.parse`.
- `Domain.fromDomainEndpoint` derives the wrong domain name and IAM ARN (403 Forbidden). Use `fromDomainAttributes` with an explicit ARN (done).
- Only a Collection is tagged via `__typename` when it has `collection_category`. Not yet observed live for `searchObjects` (sample showed only Archives).
- Total hit count caps at 10000 (same as Amplify).

## Possible next steps
- Verify a Collection item through `searchObjects` on the live API.
- Run the examples page against the deployed API.
- Deploy to prod (needs the prod domain endpoint).
