# Hand-off: AppSync query examples page in dlp-access-next-cdk

**Repo:** `dlp-access-next-cdk` (branch `whunter/appsync`)

## Current state

- New, untracked files: `src/app/examples/appsync-queries/` (`page.tsx`, `queries.ts`, `QueryResultCard.tsx`) and `src/lib/appsync.ts`.
- `package.json` / `package-lock.json` modified (added `aws4fetch`, `@aws-sdk/credential-provider-node`).
- No git commit made.
- `tsc --noEmit`, `lint`, and `npm run build` all clean; route confirmed dynamic/server-rendered.

## Not yet done

- Not tested against a live AppSync endpoint. `APPSYNC_API_URL` env var still needs to be set from the `GraphQLApiUrl` CDK output of the stack built in the companion `2026-08-05-appsync-cdk` session, once that stack is deployed.
- No commit/PR created.

## Next steps

1. Deploy the CDK stack from `../2026-08-05-appsync-cdk/summary.md` (or confirm it's already deployed).
2. Set `APPSYNC_API_URL` (and `AWS_REGION` if not `us-east-1`) in the environment (locally via `.env`/shell, in EB via `eb setenv`).
3. Load `/examples/appsync-queries` and confirm all 9 queries return real data instead of the "not configured" notice.
4. Commit the new files once verified, and decide whether this example page should ship long-term or be removed after validating the AppSync integration.
