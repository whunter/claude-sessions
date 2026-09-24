# Handoff: data-layer-provision

Repo: `~/dev/dlp/access/dlp-access-next-cdk`, branch `whunter/multi-env` (created from `whunter/appsync`). Working tree clean, **not pushed**.

## What this work is

A team lead asked for the CDK app to support several environments (`dev`, `pre-production`, `production`, feature) by **provisioning** its own DynamoDB tables, OpenSearch domain and OpenSearch streaming Lambda, where before it imported the Amplify vtdlpdev resources. The request is at `~/Desktop/provisioning_request.md`. A grilling session settled the design, and the implementation is done and committed.

## Where the details live (read these; they aren't repeated here)

- **Spec with every decision, user story, test seam and out-of-scope item:** `docs/issues/multi-env-data-layer.md`. It records the deviations made during implementation: no domain resource policy, the handler re-raising errors, the index template, and dev changed to RETAIN.
- **Commands, naming rules, architecture and gotchas:** `CLAUDE.md` at the repo root.
- **Commits:** `git log whunter/appsync..whunter/multi-env` (3 commits: spec, implementation, dev → RETAIN).
- **Code:**
  - `infra/lib/environments.ts` (config map)
  - `infra/lib/models.ts`
  - `infra/lib/data-stack.ts`, `infra/lib/api-stack.ts`, `infra/lib/app.ts`
  - `infra/lambda/opensearch-streaming/` (Amplify handler, vendored)
  - `infra/lambda/opensearch-index-template/`
- **Tests:**
  - `cd infra && npm test`: Jest, 19 passing.
  - `npm run test:lambda`: pytest, 7 passing. Needs `infra/.venv`, which exists locally and is gitignored.
- **Memory:** `~/.claude/projects/-Users-whunter-dev-dlp-access-dlp-access-next-cdk/memory/multi-env-provisioning.md` holds the grilling decisions and live vtdlpdev facts. The spec and code are authoritative if it ever disagrees with them.

## State and next steps

Nothing is deployed yet. Claude can't run deploys, because the auto-mode classifier blocks them; give the user `!` commands instead.

1. The user runs `! cd infra && npx cdk deploy --all -c env=dev`. Domain creation takes about 15–20 minutes.
2. Put a few Archive and Collection records into the `*-dlpnext-dev` tables. Check that the `archive` and `collection` indices appear (1 shard, 0 replicas, green), and that the failure queue (output `OpenSearchStreamingFailureQueueUrl`) stays empty.
3. Set `APPSYNC_API_URL` to the Api stack's `GraphQLApiUrl` and run the demo page `/examples/appsync-queries`.
4. Point the EB config template `dev-env-sc` (app `dlp-access-next`) at the `EbInstanceProfileName` output (`dlp-access-next-dev-eb`). It currently uses the account-wide default EB role.
5. Once dev is verified, the user runs `! cd infra && npx cdk destroy DlpAccessNextAppSyncStack`. That is the old import-based stack; it owns only the API, not Amplify data.
6. Deploy `pre-production` after that. Leave `production` alone: it's in a separate account, and its placeholder account ID in `environments.ts` throws at synth on purpose.
7. Ask the user before pushing or opening a PR.

## Things to watch

- AWS CLI access works through the user's login; if a call fails, ask them to run `! aws sso login`. My IAM user can't read inline role policies (`iam:GetRolePolicy` is denied).
- The EB instance role copies the managed policies from the default EB role and adds `AmazonEC2ContainerRegistryReadOnly`, standing in for an inline `ElasticBeanstalkECRRead` policy on the default role that I couldn't read. If EB instances fail to pull from ECR, that's the likely cause.
- The streaming handler works out the index name from the table name's first `-` segment, so table names must stay `<Model>-...`.
- The event source mappings start at `LATEST`, so rows written before the Api stack existed are never indexed. A backfill tool is out of scope for now.
- User preferences (from the global CLAUDE.md): commit after every turn; never push without asking; no AI attribution in commits, PRs or code.

## Suggested skills

- `mattpocock-skills:diagnosing-bugs`: if the dev deploy or streaming indexing fails.
- `code-review`: review `whunter/appsync..whunter/multi-env` before a PR.
- `mattpocock-skills:grilling`: for decisions still ahead (production sizing against the real production domain, ingest cutover, backfill tool).
- `run`: to drive the Next.js demo page against the new API.
