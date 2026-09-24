# Session summary: data-layer-provision (2026-09-24)

Repo: `dlp-access-next-cdk`, branch `whunter/multi-env` (from `whunter/appsync`). Not pushed, not deployed.

## Goal

The team lead asked for the CDK app to support multiple environments (`dev`, `pre-production`, `production`, feature) by provisioning its own DynamoDB tables, OpenSearch domain and OpenSearch streaming Lambda, configured as close to the existing Amplify services as possible. Until now it imported the Amplify vtdlpdev resources.

## How it went

1. **Grilling (3 rounds)** to settle the design. Answers from the user:
   - Amplify keeps running alongside, and the CDK environments hold separate data.
   - Production is in a separate AWS account.
   - One data/API stack per environment, shared by every Next.js branch deployment, not one per branch.
   - New environments start empty, and ingest fills them.
   - Match Amplify where it affects data or queries; modernize what clients can't see.
   - Don't index Partner.
   - The rest of my recommendations were accepted (see the spec).
2. **Pulled the live vtdlpdev config** after the user logged in to AWS:
   - Tables: all 7 have hash key `id`, `NEW_AND_OLD_IMAGES` streams and on-demand billing.
   - Domain: Elasticsearch 7.10 on 1 × t2.small, dynamic mappings only, no encryption.
   - Streaming Lambda: Amplify's python3.8 handler, which also streams Partner, sends `_type`, and retries forever.
   - The local Amplify backend checkout turned out to be out of date compared to the deployed backend.
3. **Wrote the spec** with `to-spec` to a local file, since no issue tracker is set up for these skills: `docs/issues/multi-env-data-layer.md`. Commit `2b5995f`.
4. **Implemented it** (commit `d15104b`):
   - A config map for the environments.
   - `DlpAccessNext-<env>-Data`: the tables, an encrypted OpenSearch 2.19 domain, and an index-template custom resource.
   - `DlpAccessNext-<env>-Api`: the AppSync API, Amplify's streaming handler on python3.12 with bounded retries, bisect and an SQS failure queue, and a per-environment EB instance role and profile.
   - The Amplify import mode was removed.
   - The first test suites in the repo: Jest template assertions per environment (19 tests) and pytest for the handler (7 tests), all passing.
   - CLAUDE.md updated.
5. **Refactor at the user's request** (commit `8b26bac`): `dev` now keeps its data the same way as `pre-production` and `production`. Only `f-*` feature environments are deleted with their stacks.

## Changes from the spec made during implementation (recorded in the spec)

- The search domain has no resource policy. In the same account an Allow-only policy restricts nothing, and naming the Api stack's roles from the Data stack creates a circular dependency between the stacks. Access comes only from IAM grants on the roles.
- The handler now re-raises errors. Amplify's version swallowed them, so the retry, bisect and failure-queue settings would never have triggered.
- An index template sets `auto_expand_replicas: 0-1`, so single-node clusters are green.
- Cross-stack references are pinned to `strong` in `cdk.json`.

## Open items

These are the next steps in `handoff.md`:
1. Deploy `dev` (user-run).
2. Verify indexing and the demo page.
3. Repoint the `dev-env-sc` EB template at the new instance profile.
4. Destroy the old `DlpAccessNextAppSyncStack`.
5. Deploy `pre-production`.

Production waits on its account ID. Backfill, the ingest cutover and CI/CD are out of scope.
