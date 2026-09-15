# Hand-off: Elastic Beanstalk deploy config for dlp-access-next

**Repo:** `dlp-access-next-cdk` (branch `whunter/appsync`, environment `appsync-stack`)

## Current state

- `next.config.ts` modified: removed `output: "standalone"` (was incompatible with `next start`, which the EB Node.js platform relies on; confirmed by an explicit Next.js runtime warning during local testing).
- `.gitignore` modified: added `!.elasticbeanstalk/config.yml` so the branch→environment/platform/region mapping is tracked instead of accidentally ignored by the EB CLI's default ignore rules.
- Both changes uncommitted (`M .gitignore`, `M next.config.ts`, `?? .elasticbeanstalk/`); no `eb deploy` run.
- Confirmed correct and left unchanged: `next start` honors the EB-injected `PORT` env var automatically (no explicit `-p`/`--host` needed); `next`/`react`/`react-dom` are correctly in `dependencies` so they survive the platform's `npm install --production`; the `.platform/hooks/prebuild/01_build.sh` prebuild hook handles the full `npm ci && npm run build`; runtime env vars like `APPSYNC_API_URL` are read server-side at request time so can be set via `eb setenv` independent of build/deploy.

## Not yet done

- No commit made.
- No `eb deploy` run — recommended command is `eb deploy --staged --timeout 15` (staged to pick up the uncommitted fixes; extended timeout because the on-instance `npm ci && next build` can exceed the default 5-minute CLI wait).
- Instance size for the `appsync-stack` environment not verified — flagged risk that a `t3.micro` (1GB RAM) could OOM during `next build` on the instance; needs ≥ `t3.small`.

## Next steps

1. Commit `next.config.ts` and `.gitignore`, or deploy staged first if verifying live is preferred.
2. Confirm/upgrade the EC2 instance type on `appsync-stack` to at least `t3.small` before deploying, to avoid an on-instance build OOM.
3. Run `eb deploy --staged --timeout 15` and watch the deploy logs for the prebuild hook's `npm ci && npm run build` step.
4. Set `APPSYNC_API_URL` (and `AWS_REGION` if needed) via `eb setenv` once the companion AppSync CDK stack (`2026-08-05-appsync-cdk`) is deployed, so the example page from `2026-08-05-appsync-queries-page` works in this environment.
