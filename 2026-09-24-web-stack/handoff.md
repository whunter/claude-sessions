# Handoff: per-branch Next.js Web stack (dlp-access-next-cdk)

Repo: `~/dev/dlp/access/dlp-access-next-cdk`, branch `whunter/multi-env`. The working tree is clean. HEAD is `c9e6b85` (README rewrite), one commit ahead of origin and not pushed. No PR is open. `whunter/appsync` is not merged to `main`, so a PR against `main` would also carry its commits.

## Where the details live (not repeated here)

- **Human-facing overview**: `README.md` (environments, stacks, local run, deploy commands, tests).
- **Commands, context flags, naming rules and architecture**: `CLAUDE.md` at the repo root. It covers `-c env`, `-c branch`, `-c backend=attach|provision`, and how Web stacks find their environment through the SSM parameter and the instance profile name.
- **Data-layer spec and its deviations**: `docs/issues/multi-env-data-layer.md`. The Web stack has no spec of its own; its design is in the `cf56eda` commit message and in CLAUDE.md.
- **Commits**: `git log whunter/appsync..whunter/multi-env`
  - `2b5995f` spec
  - `d15104b` data layer
  - `8b26bac` dev set to RETAIN
  - `cf56eda` Web stack
  - `c2c4173` fix for the service-role policy ARN
  - `c9e6b85` README rewritten for the project (environments, stacks, local run, deploy, tests)
- **Code**:
  - `infra/lib/web-stack.ts`: WebStack, `branchSlug`, `webResourceName`, `SOLUTION_STACK`, `BUNDLE_EXCLUDES`.
  - `infra/lib/app.ts`: `buildApp(app, { env, branch, backend })`.
  - `infra/lib/environments.ts`: the `web.instanceType` setting, `ebInstanceProfileName` and `graphqlApiUrlParameterName`.
  - `infra/lib/api-stack.ts`: now writes the SSM parameter.
- **Tests**: `cd infra && npm test` (Jest, 31 pass) and `npm run test:lambda` (pytest, 7 pass).
- **This session's summary**: `~/dev/dlp/claude-sessions/2026-09-24-web-stack/summary.md`.
- **Previous handoff and summary for the data-layer work**: `~/dev/dlp/claude-sessions/2026-09-24-data-layer-provision/`.

## What happened this session

1. The user asked for a separate stack that deploys the Next.js app to Elastic Beanstalk. When deploying, they choose whether it attaches to an existing environment's stacks or provisions new ones. I built `DlpAccessNext-Web-<branch-slug>`:
   - One Beanstalk application plus a single-instance Node.js 24 environment per branch, both named `dlpnext-<slug>`.
   - The repo source is uploaded as an S3 asset, and the existing `.platform` prebuild hook builds it.
   - The stack sets `APPSYNC_API_URL` from the SSM parameter.
   - It uses the environment's `dlp-access-next-<env>-eb` instance profile and has its own service role.
2. The user's first deploy failed: `AWSElasticBeanstalkEnhancedHealth` lives at `policy/service-role/...`. I fixed that and added a test (`c2c4173`).
3. **Current live state (dev account)**:
   - `DlpAccessNext-dev-Data`, `DlpAccessNext-dev-Api` and `DlpAccessNext-Web-whunter-multi-env` are `CREATE_COMPLETE`.
   - The EB environment `dlpnext-whunter-multi-env` is Ready / Green, at CNAME `dlpnext-whunter-multi-env.eba-jmhckmmw.us-east-1.elasticbeanstalk.com`.
   - The old `DlpAccessNextAppSyncStack` still exists.

## Next steps (none requested yet; ask the user before acting)

1. Verify the deployed app end to end:
   - Open `http://<CNAME>/examples/appsync-queries`.
   - The dev tables are empty, so expect "skipped" entries rather than errors. Seed a few Archive/Collection rows to check the search path and the indexing (see the checks in the previous handoff).
   - If requests fail with AccessDenied, check that the instance role grant and the SSM value point at the dev API.
2. Destroy the old `DlpAccessNextAppSyncStack` once dev checks out (user-run): `! cd infra && npx cdk destroy DlpAccessNextAppSyncStack`. If the CLI requires context, try adding `-c env=dev`. The old hand-made EB env `appsync-stack` (app `dlp-access-next-cdk`) still points at the old API, so the user decides whether to retire it too.
3. Items the user may want next, not yet discussed:
   - HTTPS, a load balancer or a custom domain / Route 53 record (the Web stack has none).
   - Wiring `.github/workflows/pr-preview-*.yaml` to use the Web stack. Those workflows build a Docker image from a Dockerfile that doesn't exist in the repo, so they are likely stale.
   - Deploying `pre-production`.
4. Open a PR only when asked.

## Things to watch

- Deploys are user-run; give the user `!` commands. Never push without asking, except when "write a summary" is requested. Commit after every turn. Add no AI attribution anywhere (the user's global CLAUDE.md).
- My IAM user cannot call `ssm:GetParameter` or `iam:GetRolePolicy`. Read the API URL from the Api stack output `GraphQLApiUrl` instead.
- **Beanstalk platform pin**: `SOLUTION_STACK` is `v6.11.8`. Managed minor updates move the live platform forward, so bump the constant when it is changed deliberately.
- Attach mode requires the target environment's Api stack from `cf56eda` or later (that version writes the SSM parameter). Otherwise the deploy fails with "Unable to fetch parameters".
- **Asset staging**: tests and synth stage a copy of the repo into `cdk.out` or a temp directory. Root `npm run lint` already fails on generated JS under `infra/cdk.out`. That was not caused by this work, but could be fixed by adding `infra/**` to the root ESLint ignores.
- A first-create failure leaves the stack in `ROLLBACK_COMPLETE`. CDK deletes and recreates it on the next deploy.

## Suggested skills

- `run`: drive the deployed app or local Next.js against the dev API to verify the demo page.
- `mattpocock-skills:diagnosing-bugs`: if the EB app or AppSync calls fail after deploy.
- `code-review` or `mattpocock-skills:code-review`: review `whunter/appsync..whunter/multi-env` before a PR.
- `mattpocock-skills:grilling`: before designing HTTPS/domain support or CI integration for Web stacks.
- `mattpocock-skills:wizard`: if the user wants a guided script for the manual cutover steps (destroying old stacks, retiring the `appsync-stack` EB env).
