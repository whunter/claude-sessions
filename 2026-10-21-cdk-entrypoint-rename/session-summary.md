# Session summary: cdk-entrypoint-rename (2026-10-21)

**Repo:** `dlp-access-next-cdk`, branch `whunter/appsync` (commit `39f2aca`, not pushed)

## What was asked and what happened

1. **Is `infra/bin/appsync.ts` named accurately?** No. It's the CDK app's entry point, which calls `buildApp` from `lib/app.ts` and adds the Data, Api, Auth and Web stacks, not just AppSync.
   - Recommended `bin/dlp-access-next.ts`, which follows `cdk init`'s `bin/<project>.ts` convention and the `DlpAccessNext-*` stack prefix.
   - Advised against renaming `lib/api-stack.ts` to `appsync.ts`. It matches `data-stack.ts`, `auth-stack.ts` and `web-stack.ts`, and is named after the `DlpAccessNext-<env>-Api` stack. That stack also holds the streaming Lambda, the SQS failure queue, the Beanstalk instance role and an SSM parameter. `src/lib/appsync.ts` already exists in the Next.js app.

2. **Renamed it** (`39f2aca`).
   - `git mv` to `infra/bin/dlp-access-next.ts`, and updated `infra/cdk.json`.
   - Renamed the package in `infra/package.json` and `package-lock.json` to `dlp-access-next-infra`.
   - `npm test` passed (152 tests in 4 suites). `cdk ls` with dev's options, using a placeholder account and pool, listed the three dev stacks through the new entry point.

3. **Why did the attach deploy fail with "Unable to fetch parameters"?** The command was correct, but dev's backend had been destroyed.
   - CloudFormation history: the dev Data stack's tables were created at 19:32 UTC on 2026-10-20 and the `whunter-appsync` Web stack at 19:52. Dev's Api, Auth and Data stacks were deleted between 21:05 and 21:07.
   - The three SSM parameters belong to the Api and Auth stacks, so they went with them.
   - The surviving Web stack is broken, since its API and instance profile are gone.
   - The seven dev tables were kept (tier removal policy) and will block re-creating the Data stack.
   - Gave the user a loop to turn off deletion protection and delete the tables, and the `-c backend=provision` deploy command. Neither was run by Claude.
   - Noted a gap: the deploy check doesn't look up the backend stacks in attach mode, so it couldn't warn about this. Offered a fix, not started.
