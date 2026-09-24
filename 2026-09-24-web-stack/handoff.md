# Handoff: per-branch Next.js Web stack (dlp-access-next-cdk)

Repo: `~/dev/dlp/access/dlp-access-next-cdk`, branch `whunter/multi-env`. The working tree is clean. HEAD is `cd58306`, four commits ahead of origin (`df831d2`, `2f89eb8`, `3e556bd`, `cd58306`) and not pushed. No PR is open. `whunter/appsync` is not merged to `main`, so a PR against `main` would also carry its commits.

## Where the details live (not repeated here)

- **Human-facing overview**: `README.md` (environments, stacks, local run, deploy commands, tests).
- **Commands, context flags, naming rules and architecture**: `CLAUDE.md` at the repo root. It covers `npm run deploy`, `-c env`, `-c account`, `-c production`, `-c branch`, `-c backend=attach|provision`, and how Web stacks find their environment through the SSM parameter and the instance profile name.
- **Data-layer spec and its deviations**: `docs/issues/multi-env-data-layer.md`. The Web stack has no spec of its own; its design is in the `cf56eda` commit message and in CLAUDE.md.
- **Commits**: `git log whunter/appsync..whunter/multi-env`
  - `2b5995f` spec
  - `d15104b` data layer
  - `8b26bac` dev set to RETAIN
  - `cf56eda` Web stack
  - `c2c4173` fix for the service-role policy ARN
  - `c9e6b85` README rewritten for the project (environments, stacks, local run, deploy, tests)
  - `b63f444` the AWS account ID comes from a required `-c account=<12 digits>` instead of being hardcoded in `environments.ts`
  - `c9df390` dummy account ID (`123456789012`) in the streaming handler's test ARN
  - `30fd263` README notes that the account is passed in
  - `df831d2` `-c production=true|false` (default false) picks the sizing: 3 × `m7g.medium.search` across 3 AZs and a `t3.medium` Beanstalk instance, instead of 1 × `t3.small.search` and `t3.small`
  - `2f89eb8` `npm run deploy` wrapper: validates the options, prints them and the stacks, and runs `cdk deploy --all` only on `y`/`yes`
  - `3e556bd` bold red production banner in that confirmation
  - `cd58306` README production deploy example
- **Code**:
  - `infra/lib/web-stack.ts`: WebStack, `branchSlug`, `webResourceName`, `SOLUTION_STACK`, `BUNDLE_EXCLUDES`.
  - `infra/lib/app.ts`: `planApp(options)` validates `{ env, account, production, branch, backend }` and returns the stack names; `buildApp` builds from it. `optionsFromContext` and `booleanContext` parse context for both entry points.
  - `infra/bin/deploy.ts` and `infra/lib/deploy.ts`: the confirmation wrapper (`contextFromArgs`, `describePlan`, `productionWarning`, `isConfirmed`).
  - `infra/lib/environments.ts`: per-environment region and removal policy (no account IDs), the `STANDARD_SIZING` and `PRODUCTION_SIZING` profiles, `ebInstanceProfileName` and `graphqlApiUrlParameterName`.
  - `infra/lib/api-stack.ts`: now writes the SSM parameter.
- **Tests**: `cd infra && npm test` (Jest, 69 pass across `app.test.ts` and `deploy.test.ts`) and `npm run test:lambda` (pytest, 7 pass).
- **CDK lesson** (traces one deploy command through every step): `~/dev/dlp/claude-sessions/2026-09-24-web-stack/cdk-lesson.md`, plus `cdk-lesson.html`. Rebuild the HTML with `/usr/bin/python3 md2html.py cdk-lesson.md cdk-lesson.html` (that Python has markdown-it-py).
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
4. The user asked for a lesson on how the CDK scripts work. I wrote `cdk-lesson.md` and an HTML version in this session directory, along with the `md2html.py` converter.
5. The user didn't want AWS account IDs hardcoded. `-c account` is now required on every CDK command (`b63f444`). The real ID is gone from the repo's files (it remains in git history). The docs and the lesson were updated to match.
6. At the user's request, added `-c production` (default false) for production sizing (3 OpenSearch nodes instead of 1, `t3.medium` instead of `t3.small`). Sizing is no longer tied to the environment name.
7. The user asked for a confirmation before anything reaches AWS. The CDK app can't prompt (the CLI runs it with stdin closed), so `npm run deploy` does it: it shows the plan and deploys only on `y`/`yes`. With `env=production` it first prints a red warning banner naming the account, and flags a missing `-c production=true`. The lesson now covers this as Step 0.

## Next steps (none requested yet; ask the user before acting)

1. Verify the deployed app end to end:
   - Open `http://<CNAME>/examples/appsync-queries`.
   - The dev tables are empty, so expect "skipped" entries rather than errors. Seed a few Archive/Collection rows to check the search path and the indexing (see the checks in the previous handoff).
   - If requests fail with AccessDenied, check that the instance role grant and the SSM value point at the dev API.
2. Destroy the old `DlpAccessNextAppSyncStack` once dev checks out (user-run): `! cd infra && npx cdk destroy DlpAccessNextAppSyncStack -c env=dev -c account=$(aws sts get-caller-identity --query Account --output text)`. The app now throws without `env` and `account`, so the CLI likely needs both even though that stack isn't in the app. The old hand-made EB env `appsync-stack` (app `dlp-access-next-cdk`) still points at the old API, so the user decides whether to retire it too.
3. Items the user may want next, not yet discussed:
   - HTTPS, a load balancer or a custom domain / Route 53 record (the Web stack has none).
   - Wiring `.github/workflows/pr-preview-*.yaml` to use the Web stack. Those workflows build a Docker image from a Dockerfile that doesn't exist in the repo, so they are likely stale.
   - Deploying `pre-production`.
4. Push `whunter/multi-env` (four commits ahead) and open a PR only when asked.

## Things to watch

- Deploys are user-run; give the user `!` commands. Never push without asking, except when "write a summary" is requested. Commit after every turn. Add no AI attribution anywhere (the user's global CLAUDE.md).
- Deploy through `npm run deploy -- <cdk args>`, which the user runs, since it prompts. `npx cdk deploy` still works but skips the confirmation.
- Production sizing needs `-c production=true`; `-c env=production` alone gets the small sizing.
- Every CDK command needs `-c account=<id>`. Nothing checks that the account matches the environment, so a wrong ID deploys that environment into the wrong account.
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
