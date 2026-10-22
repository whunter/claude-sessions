# Hand-off: deploy-cli rename

**Branch:** `whunter/feature/add/deployment` in `dlp-access-next-cdk`
**State:** rename committed locally as `f66b0b8`; the branch is not pushed.

## Done

- `infra/lib/deploy.ts` is now `infra/lib/deploy-cli.ts`; the test is `infra/test/deploy-cli.test.ts`. Imports updated; type-check and tests pass.

## Open items

- `infra/lib/deploy-check.ts` has an uncommitted change that was there before this session. It was left out of the rename commit on purpose. Review and commit it separately.
- The `CLAUDE.md` update (`infra/lib/deploy.ts` → `infra/lib/deploy-cli.ts`) exists only on this machine because `CLAUDE.md` isn't tracked.
- Push the branch when ready, then open the GitHub PR from `2026-10-22-cdk-pr/pull-request.md` (it needs no changes for this rename).
