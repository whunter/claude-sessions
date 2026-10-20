# Hand-off: appsync-testing (2026-10-20)

**Repo:** `~/dev/dlp/access/dlp-access-next-cdk`, branch `whunter/appsync` (clean, last commit `44924ca`, 6 commits not pushed)

## State

- **Deploy script** (`infra/bin/deploy.ts`):
  - It deploys the commit at HEAD, never the working tree.
  - Before the prompt it shows the plan, the commit, uncommitted changes, and a create/update check of each stack with warnings.
  - `--yes` (CI only) skips the prompt. `--no-check` skips the check.
- **Docs:** `docs/deployment.md` covers create, redeploy and destroy for backends and frontends, plus a CI section. `CLAUDE.md` is updated to match.
- **dev account (226388486048, us-east-1):**
  - The seven orphaned `*-dlpnext-dev` tables were deleted.
  - When last checked, dev's Data, Api and Auth stacks were `CREATE_COMPLETE`, and `DlpAccessNext-Web-whunter-appsync` was `CREATE_IN_PROGRESS`, presumably from the user's own deploy.
  - dev's Auth stack records user pool `us-east-1_wy1lPpMYt` and identity provider `VT-SSO-OIDC`.

## Next steps

1. Push `whunter/appsync` when ready (not pushed by Claude).
2. Check that the `whunter-appsync` frontend finished deploying and that sign-in works at `https://whunter-appsync.dlp-access-dev.dlp.cloud.lib.vt.edu`.
   - This also closes the open item in `.scratch/code-review-fixes/issues/05-cognito-client-secret-out-of-plaintext.md`, from the previous session.
3. Redeploy existing frontends so they get the new `Branch` output. Until then, the slug-collision warning is skipped for them.
4. Remember to pass `-c identityProvider=VT-SSO-OIDC` on every dev backend deploy. The new check now warns when it's missing.

## Open options (offered, not started)

- A GitHub Actions workflow: GitHub Environments, OIDC deploy role, `cdk diff` on pull requests, and approval-gated deploys. `docs/deployment.md` has an untested example job.
- Compare a frontend's Beanstalk instance size in the check. Today only search sizing is compared for `production=true`.

## Caveats

- The check needs the `aws` CLI and permission to describe stacks, DynamoDB tables, the OpenSearch domain and Beanstalk applications. A missing permission shows up as a warning, not an error.
- The deploy uses whatever commit is checked out, even if `-c branch` names a different branch.
- A frontend whose HEAD files haven't changed produces the same bundle, so it isn't redeployed.
