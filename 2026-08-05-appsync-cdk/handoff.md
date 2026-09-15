# Hand-off: AppSync CDK stack for dlp-access-next

**Repo:** `dlp-access-next-cdk` (branch `whunter/appsync`)

## Current state

- New `infra/` directory (self-contained TypeScript CDK v2 app) is untracked, not yet committed.
- Stack (`AppSyncStack`) builds a read-only, IAM-authorized AppSync API (`dlp-access-next-vtdlp`) over the existing `vtdlpdev` DynamoDB tables, with 27 hand-generated APPSYNC_JS resolvers, and grants `appsync:GraphQL` to the real `aws-elasticbeanstalk-ec2-role`.
- Verified with `tsc --noEmit` and `cdk synth` (resource counts match expectations); `cdk.out/` synth artifacts were deleted after verification and `infra/.gitignore` added.
- Not yet deployed — no `cdk deploy` was run.

## Not yet done

- No git commit made.
- No deploy to AWS.
- Prod tables (suffix `77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd`) were discovered during investigation but intentionally not wired up — dev-only scope for now.

## Next steps

1. Review `infra/lib/appsync-stack.ts` and `infra/schema/schema.graphql`, then commit `infra/` to the branch.
2. Deploy: `cd infra && npm install && npx cdk deploy` (defaults to account `226388486048`, region `us-east-1`, `vtdlpdev` tables).
3. Capture the `GraphQLApiUrl` CDK output and feed it into `APPSYNC_API_URL` for the Next.js app — see the companion `2026-08-05-appsync-queries-page` session, which built a page that consumes this exact API and is waiting on this env var.
4. When ready for production, re-run `cdk deploy -c tableSuffix=77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd` (or parameterize an environment-specific deploy) — not yet tested against prod tables.
