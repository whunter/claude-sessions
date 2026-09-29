# Session summary: stack drift blocking `amplify gen2-migration lock` (2026-09-29)

Repo: `~/dev/dlp/access/dlp-access`, branch `whunter/upgrade/amplify-gen-2`. Amplify Gen 1 env `gentwo` (app `vtdlp-dev`, stack `amplify-vtdlpdev-gentwo-c4fb8`, us-east-1).

## Goal

Get `amplify gen2-migration lock` past its drift validation. The user had changed the AppSync API key's expiration by hand. They then ran `amplify push` and redeployed a branch from the Amplify console, hoping that would reset it.

## What happened

### 1. Resource drift on the API key (AppSync rounds expiration to the hour)
- Lock reported CloudFormation drift on `GraphQLAPIDefaultApiKey215A6DD7` `/Expires`. Deployed was `1791277200`; the template expected `1791280228`.
- The deployed value is the template value rounded **down to the hour**. The earlier push had reset the manual edit. The remaining drift comes from AppSync, which truncates API key expiration to the hour. Amplify writes `now + N days` to the second, so every deploy drifts.
- **Fix:** `amplify/backend/api/vtdlp/override.ts` now sets the key's `expires` to `now + expirationDays`, rounded down to the hour.
- **Gotcha:** the type definitions (`@aws-amplify/cli-extensibility-helper`) name the key `resources.api.GraphQLAPIDefaultApiKey`, but at runtime it is `GraphQLAPIDefaultApiKeyDefaultApiKey`. Using the typed name does nothing. The real names were found by dumping `Object.keys(resources.api)` into CFN metadata, because `console.log` and thrown messages from overrides are swallowed.
- `amplify api gql-compile` does **not** run overrides; `amplify build` and `amplify push` do.
- Claude's `amplify push` was blocked by the permission check, so the user pushed. They also changed `expirationDays` from 7 to 90.

### 2. Template drift: stale template in S3
- Lock then reported "Template Drift: S3 and deployed templates differ", again only for the API key's `Expires`.
- The deployed API nested stack and `#current-cloud-backend.zip` both had `1798452000` (Dec 28 2026 10:00 UTC, on the hour).
- `s3://amplify-vtdlpdev-gentwo-c4fb8-deployment/amplify-cfn-templates/api/cloudformation-template.json` had `1791283977`: 10:52:57 UTC plus 7 days, not rounded. It was written at 10:53:00, about 2 minutes after the push deployed the nested stack. So something regenerated the template with default settings and no override, then uploaded it without deploying. What did this was not identified. Lock itself does not rewrite the file.
- The local staged `amplify/backend/awscloudformation/build/api/vtdlp/build/cloudformation-template.json` was checked to be identical to the deployed template.
- **Fix (done by the user; Claude's S3 write was blocked):** backed up the stale object to `/tmp/api-template.stale.json`, then uploaded the staged template over it.

### 3. Result
- The S3 template now has `1798452000`. `amplify gen2-migration lock` passes validation and shows its plan. It stopped at "Do you want to continue?" because Claude's shell is non-interactive.
- **The lock was not applied** in this session.

## Files changed

- `dlp-access/amplify/backend/api/vtdlp/override.ts`: API key expiry rounded to the hour. `amplify/` is gitignored, so this is only in the local tree and in `#current-cloud-backend.zip`, not in git.
