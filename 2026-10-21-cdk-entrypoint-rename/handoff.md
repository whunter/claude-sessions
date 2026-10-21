# Hand-off: cdk-entrypoint-rename (2026-10-21)

**Repo:** `~/dev/dlp/access/dlp-access-next-cdk`, branch `whunter/appsync` (clean, last commit `39f2aca`, not pushed)

## State

- **CDK entry point renamed** (`39f2aca`): `infra/bin/appsync.ts` is now `infra/bin/dlp-access-next.ts`.
  - `infra/cdk.json` runs the new file.
  - The infra package is named `dlp-access-next-infra` (was `dlp-access-next-appsync-infra`).
  - `lib/api-stack.ts` keeps its name. It matches its siblings and the `DlpAccessNext-<env>-Api` stack, and holds more than AppSync.
- **dev account (226388486048, us-east-1) has no backend:**
  - `DlpAccessNext-dev-Api`, `-Auth` and `-Data` were deleted on 2026-10-20 between 21:05 and 21:07 UTC.
  - `DlpAccessNext-Web-whunter-appsync` still exists (`CREATE_COMPLETE`, created 19:52 UTC). It's broken: its API, SSM parameters and instance profile `dlp-access-next-dev-eb` are gone.
  - All seven `<Model>-dlpnext-dev` tables are left over (created 19:32 UTC, deletion protection on, item count 0 when checked). They will block creating a new dev Data stack.
  - No `dlpnext-dev` search domain exists.
- The user's attach deploy (`-c env=dev -c branch=...`) failed with "Unable to fetch parameters" because dev's Api and Auth stacks don't exist.

## Next steps

1. Check the leftover dev tables, then delete them (turn off deletion protection first) or import them into the Data stack. Claude gave the user a loop to delete them but didn't run it.
2. Redeploy dev's backend and the branch together (user-run, from `infra/`):
   `npm run deploy -- -c env=dev -c account=$ACCOUNT -c branch=$(git branch --show-current) -c backend=provision -c userPool=us-east-1_wy1lPpMYt -c identityProvider=VT-SSO-OIDC`
   - The user pool ID is the one dev's Auth stack recorded in the previous session. Confirm it before using it.
3. Push `whunter/appsync` when ready.

## Open options (offered, not started)

- Have the deploy check warn in attach mode when the environment's Api or Auth stack is missing. Today `lookupDeployedState` in `infra/lib/deploy-check.ts` only looks up the stacks in the plan, so an attach deploy to a destroyed backend passes the check and fails in CloudFormation.

## Caveats

- `vtdlp-whunter-workload` can't call `ssm:GetParametersByPath`, so Claude couldn't list the parameters directly. The CloudFormation stack history was enough to find the cause.
