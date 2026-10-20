# Session summary: appsync-testing (2026-10-20)

**Repo:** `dlp-access-next-cdk`, branch `whunter/appsync` (commits `9f85a1f`..`44924ca`, not pushed)

## What was asked and what happened

1. **How to tear down and recreate the dev backend.** Explained the `cdk destroy` and `npm run deploy` commands.
   - `cdk destroy` needs `-c userPool` only because the app checks it whenever the backend stacks are in the app. The pool itself is never deleted: the Auth stack holds only two SSM parameters.
   - Destroy a backend's frontends before the backend.
   - Tier tables (`dev`, `pre-production`, `production`) are kept when the backend is destroyed, and block re-creating it.

2. **Deployment documentation.** Wrote `docs/deployment.md`: commands and notes for creating, redeploying and destroying backends and frontends, separately and together.
   - Finding a backend's frontends uses each Beanstalk application's description, `using the <env> environment`. The first draft queried the stack description, which is wrong, and was fixed.

3. **Deploy the most recent commit, not the working tree** (`c95f556`).
   - The Web stack bundles HEAD with `git archive` at synth time, excluding `infra`, docs, Markdown, `.scratch` and `.env*`.
   - The Beanstalk application version's description records the commit.
   - `npm run deploy` prints the commit it will deploy and lists uncommitted changes it is leaving out.
   - New tests check that untracked and modified files are left out.

4. **CI mode** (`dbd49d9`, `d3b79ac`).
   - Discussed best practice: approve in the pipeline (GitHub Environments with required reviewers), not by piping `y` into a prompt.
   - Added `--yes`/`-y` to the deploy script. It is accepted only when `CI` is `true` or `1`, and is removed before calling `cdk deploy`. It adds `--require-approval never` unless a `--require-approval` is given.
   - Added a "Running in CI" section to `docs/deployment.md`, with pipeline notes and an example GitHub Actions job. The example hasn't been run.

5. **Published the deployment doc as an artifact page, then deleted it** at the user's request. The content stays in `docs/deployment.md`.

6. **Deleted the orphaned `*-dlpnext-dev` DynamoDB tables** in account 226388486048 (us-east-1): Archive, Collection, History, MetadataField, PageContent, Partner and Site.
   - Before deleting, confirmed that no stack owned them and that a scan found every table empty.
   - They had made the `DlpAccessNext-dev-Data` create fail at CloudFormation's early "resource exists" check.

7. **Create/update check before confirming a deploy** (`44924ca`).
   - New `infra/lib/deploy-check.ts` looks up what is deployed with the `aws` CLI and lists each stack as `create`, `update` or `busy`.
   - It warns about:
     - a repointed user pool, or a changed identity provider
     - a resized search domain (hints at a missing `-c production=true`)
     - a frontend moving to another environment
     - a branch name whose slug belongs to a frontend deployed from another branch name
     - leftover tables or a search domain that block creating a Data stack
     - a stack mid-operation, and credentials for another account
   - The check never blocks a deploy. A failed lookup becomes a warning, and with warnings the prompt reads "Deploy anyway?". `--yes` in CI logs the results without stopping, and `--no-check` skips the check.
   - Web stacks now have a `Branch` stack output holding the raw branch name, which the slug-collision warning compares against.
   - Checked against the real account, answering `n`: the check caught a deliberately missing `-c identityProvider`, and reported this branch's Web stack as `CREATE_IN_PROGRESS`.

8. **Questions answered:**
   - what the `--` in `npm run deploy -- …` does. Tested: without it, npm keeps every flag for itself and the script receives none.
   - the difference between `npm` and `npx`.

## Mistake during the session

While testing `--yes`, ran `CI=true npm run deploy -- --yes …` with production options and the fake account `123456789012`. It could not deploy anything, and no `cdk deploy` process was left running. It was reported to the user.

## Verification

- `npx tsc --noEmit` passes.
- `npx jest`: 139 tests pass in 4 suites.
- No real deploy was run by Claude. All runs of the deploy script against the account were answered `n`.
