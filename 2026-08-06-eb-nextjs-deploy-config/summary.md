# Session: Elastic Beanstalk deploy config for dlp-access-next

**Date:** 2026-08-06
**Repo:** `dlp-access-next-cdk` (branch `whunter/appsync`)
**Goal:** Confirm the Elastic Beanstalk deployment configuration is correct for the Next.js app, and get the right `eb deploy` invocation.

## Starting point

Repo already had an EB setup in progress (prior commits this session: `wipe eb` → dropped an earlier Dockerfile-based approach in favor of the native Node.js platform; `generate lock. edit dockerfile`; `run as node?`; `remove start options`; `Add EB prebuild hook to install devDependencies and build`). Config at hand:

- `.elasticbeanstalk/config.yml` — platform "Node.js 24 running on 64bit Amazon Linux 2023", branch `whunter/appsync` → environment `appsync-stack`.
- `.platform/hooks/prebuild/01_build.sh` — runs `npm ci && npm run build` in `/var/app/staging`, because the Node.js platform only runs `npm install --production` and never a build step.
- `package.json` — `start: "next start"` (no `-p`/`--host` flags).
- `next.config.ts` — had `output: "standalone"`.

## Investigation

Walked the actual deploy lifecycle instead of trusting the files at face value:

- Confirmed `next start`'s `-p`/`PORT` option is bound via commander's `.env('PORT')`, so it automatically honors the `PORT` env var the EB Node.js platform sets for its nginx proxy (8080) — no explicit `-p`/`--host` flags needed (matches the `remove start options` commit).
- Confirmed `next`, `react`, `react-dom` are in `dependencies` (not `devDependencies`), so the app still runs after the platform's own `npm install --production` prunes dev deps post-build.
- Ran `npm ci --dry-run` — lockfile is in sync with `package.json`.
- Ran `npm run build` locally — succeeded.
- **Caught a real bug by actually running the server**: started with `PORT=8080 npm run start` and Next printed `⚠ "next start" does not work with "output: standalone" configuration. Use "node .next/standalone/server.js" instead.` The root page still returned HTTP 200 in the quick test, but the combination is explicitly unsupported by Next.js and risks breaking static asset serving on other routes.
- Since the prebuild hook already does a full `npm ci` (not a trimmed standalone install), the standalone output wasn't buying anything — removed `output: "standalone"` from `next.config.ts` instead of switching to `node .next/standalone/server.js`.
- Re-verified after the fix: rebuilt, restarted on `PORT=8080`, confirmed no warning, root page HTTP 200, and a `_next/static/*.css` asset also HTTP 200 (this specifically would be the failure mode of the standalone/`next start` mismatch).

## What was changed

1. `next.config.ts` — removed `output: "standalone"`.
2. `.gitignore` — the EB CLI boilerplate ignored all of `.elasticbeanstalk/*` except `*.cfg.yml`/`*.global.yml`, which doesn't match `config.yml` — so the file holding the branch→environment mapping, platform, and region was untracked and local-only. Added `!.elasticbeanstalk/config.yml` so it's no longer ignored (per user request). `.elasticbeanstalk/app_versions/` (cached deploy zips) remains ignored.

## Other things confirmed correct (no change needed)

- Runtime env vars (`APPSYNC_API_URL`, `AWS_REGION` in `src/lib/appsync.ts`) are read server-side at request time, not baked into the build — fine to set via `eb setenv` independent of build timing.
- `sc: git` in `config.yml` means `eb deploy` ships the last commit by default (or the git index with `--staged`), and `.next`/`node_modules` are correctly gitignored/untracked since they're rebuilt on the instance by the prebuild hook.

## Recommended deploy command

```
eb deploy --staged --timeout 15
```

- `--staged` to include the git-index changes (e.g. the `next.config.ts`/`.gitignore` fixes) without requiring a commit first.
- `--timeout 15` because the default 5-minute CLI wait can plausibly be exceeded by running `npm ci` + `next build` on the instance itself.

Flagged but not verified (outside repo scope): confirm the `appsync-stack` EC2 instance type has enough RAM (≥ `t3.small`) to survive `next build` — a `t3.micro` (1GB) risks OOMing during the on-instance build.

## State at end of session

- `next.config.ts` and `.gitignore` modified, not committed (`git status`: `M .gitignore`, `M next.config.ts`, `?? .elasticbeanstalk/`).
- No `git commit` was made — the user hadn't asked for one.
- No `eb deploy` was run.
