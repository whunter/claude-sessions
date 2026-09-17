# Handoff — appsync-key-extend (2026-09-17)

## Context

`access/dlp-access` repo, branch `whunter-refactor-appsync-extend`. Full
narrative in `summary.md` in this directory.

Goal: AppSync's dev API key was only staying alive as a side effect of
frequent CI deploys (each `amplify push` recomputes `expires = now + 7
days`). This session built real automated rotation: a scheduled Lambda
(via CDK) that mints a new key and publishes it to SSM, plus a CI build
step that syncs the frontend's baked-in key from SSM instead of trusting
whatever `amplify push` produced.

Latest commit (pushed to origin):
```
41f1e6a Add automatic AppSync API key rotation infra and CI sync step
```

## State

Working tree clean. Nothing pending to commit from this session. No PR
opened yet (link was surfaced but not used:
https://github.com/vt-digital-libraries-platform/dlp-access/pull/new/whunter-refactor-appsync-extend).

**Two things are built but intentionally NOT deployed/applied to live
AWS** — the user explicitly said "hold off" on both when asked. See
below.

## Outstanding task 1: deploy the CDK stack

Nothing rotates until this is deployed. Steps:

```bash
cd access/dlp-access/infra/appsync-key-rotation
npm install                # if node_modules isn't already present
npx cdk bootstrap           # only if this AWS account/region (226388486048 / us-east-1)
                             # hasn't been CDK-bootstrapped before; check first —
                             # bootstrapping is idempotent but worth confirming state
npx cdk deploy \
  -c apiId=77eik3yv7rbdbjhjemas6h7dmi \
  -c env=dev \
  -c alarmEmail=whunter@vt.edu
```

This creates, in account `226388486048` / `us-east-1`:
- Lambda `RotateApiKeyFunction` (Node 20.x)
- EventBridge rule on `rate(1 day)` triggering it
- IAM role scoped to `appsync:ListApiKeys`/`CreateApiKey`/`DeleteApiKey`
  on `arn:aws:appsync:us-east-1:226388486048:apis/77eik3yv7rbdbjhjemas6h7dmi`
  and `ssm:PutParameter` on `/vtdlp/dev/appsync/api-key` and
  `/vtdlp/dev/appsync/api-key-expires`
- CloudWatch alarm on Lambda errors → SNS topic → email subscription to
  whunter@vt.edu (AWS will send a subscription-confirmation email; it
  must be confirmed for alarms to actually deliver)

Optional context overrides (all have defaults — see
`bin/appsync-key-rotation.ts`): `ssmParameterName`, `keyTtlDays` (default
7), `minRemainingDays` (default 3, i.e. rotate when <3 days remain),
`scheduleExpression` (default `rate(1 day)`).

After deploying, verify:
```bash
aws ssm get-parameter --name /vtdlp/dev/appsync/api-key --with-decryption
aws ssm get-parameter --name /vtdlp/dev/appsync/api-key-expires
```
(These won't exist until the Lambda has run at least once — either wait
for the daily schedule or manually invoke
`aws lambda invoke --function-name <RotateApiKeyFunction name from the
CDK output> /tmp/out.json` to force a first run.)

**For pprd**: the pprd AppSync API id is not yet known — `aws appsync
list-graphql-apis` returned `AccessDeniedException` for the current IAM
user (`vtdlp-whunter-workload`). Look it up (console, or a role with
broader AppSync read access) before running `cdk deploy -c
apiId=<pprd-api-id> -c env=pprd -c alarmEmail=...` for the pprd app
(`d3reyduta3lkkz`).

## Outstanding task 2: wire the live Amplify Console build spec

The CI script (`scripts/sync-appsync-api-key.sh`) is landed on the
branch and is a safe no-op until this is done — it only acts if
`APPSYNC_API_KEY_SSM_PARAM` is set. The checked-in `examples/amplify.yml`
was updated as a reference but **is not** what the live app actually
runs; the real build spec lives in the Amplify Console / app config.

To activate, for app `d1n265krqy0ld3` (vtdlp-dev):

1. Add app-level (or branch-level, if you only want this on `dev`)
   environment variable:
   ```
   APPSYNC_API_KEY_SSM_PARAM=/vtdlp/dev/appsync/api-key
   ```
   Via CLI:
   ```bash
   aws amplify update-app --app-id d1n265krqy0ld3 \
     --environment-variables \
       REACT_APP_FEEDBACK_API_ENDPOINT="https://y329wzd07j.execute-api.us-east-1.amazonaws.com/padma",REACT_APP_MINT_API_KEY="CeCfZiApIs2fJXV4B2kwkar6k9GOSVc24j5eXAYQ",REACT_APP_MINT_LINK="https://9hqnlodbdj.execute-api.us-east-1.amazonaws.com/Prod/mint",REACT_APP_REP_TYPE="federated",USER_DISABLE_TESTS="true",_BUILD_TIMEOUT="120",APPSYNC_API_KEY_SSM_PARAM="/vtdlp/dev/appsync/api-key"
   ```
   (`update-app --environment-variables` replaces the whole map, so the
   existing vars are re-specified here rather than merged — re-check
   current values with `aws amplify get-app --app-id d1n265krqy0ld3
   --query app.environmentVariables` before running, in case they've
   changed since this session.)

2. Patch the build spec to add the sync step. Current live spec (as of
   this session) is in `summary.md`'s investigation notes / was fetched
   via:
   ```bash
   aws amplify get-app --app-id d1n265krqy0ld3 --query app.buildSpec --output text
   ```
   Insert `- npm run sync:appsync-key` right before `- REACT_APP_GIT_COMMIT=... npm run build`
   in the `frontend.phases.build.commands` list, then push the full spec
   back with:
   ```bash
   aws amplify update-app --app-id d1n265krqy0ld3 --build-spec file://new-buildspec.yml
   ```

3. Trigger a build (or wait for the next push) and confirm
   `src/amplifyconfiguration.json` in the build output has the SSM-sourced
   key, not whatever `amplifyPush` generated — check the build logs for
   the script's own log line: `Synced aws_appsync_apiKey in
   src/amplifyconfiguration.json from SSM parameter
   /vtdlp/dev/appsync/api-key`.

Do task 1 before task 2 — the sync script will hard-fail the build
(`error: could not read AppSync API key from SSM parameter ...`) if the
env var is set but the SSM parameter doesn't exist yet.

## If asked to open a PR

Title suggestion: "Add automatic AppSync API key rotation infra and CI
sync step". Body should summarize what's in `summary.md` and note the
two outstanding manual deploy steps above — a reviewer approving the PR
is not the same as approving the live AWS deploy, so don't fold "merge
this" into "deploy the CDK stack" without asking again.
