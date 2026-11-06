# Session summary: npm ci lockfile sync failure (amplify-build-errors)

- **Date:** 2026-11-06
- **Repo:** gen-2-dlp-access (`~/dev/dlp/access/gen-2-dlp-access`)
- **Branch:** `light-env-gen2` @ 4b331e6 (committed, **not pushed**)

## Problem

`npm install` produced a `package-lock.json` that `npm ci` rejected:

```
npm error `npm ci` can only install packages when your package.json and package-lock.json ... are in sync.
npm error Missing: @opentelemetry/core@2.0.0 from lock file
```

Depending on how the lockfile was generated, the error listed other missing entries instead (`@aws-cdk/toolkit-lib@1.19.0`, `@aws-cdk/cloud-assembly-api@2.2.0`, ...).

## What was checked

| Question | Result |
|---|---|
| Malformed `package.json`? | No. It parses, and `npm pkg fix --dry-run` finds nothing. |
| Packages need updating? | No. All `@aws-amplify/*` packages are at latest (backend 1.25.1, backend-cli 1.10.0, backend-data 1.9.0, data-construct 1.17.8, aws-amplify 6.22.2). The latest release still has the bug. |
| Packages added by Amplify? | **Root cause.** See below. |
| Bad npm version? | Not locally: the failure reproduces on npm 10.9.4, 11.6.2, 11.19.1, 11.21.2 and 12.2.2. But `amplify.yml` used Node 17.9.1 (npm 8), and npm 8 and 10 also reject npm-11 lockfiles over an optional peer (`type-fest@4.41.0`). |

## Root cause

`@aws-amplify/data-construct` (via `@aws-amplify/backend-data`) and `@aws-amplify/graphql-api-construct` publish bundled dependencies that don't agree with each other. In 1.17.4 through 1.17.8, bundled `@opentelemetry/resources@2.0.0` and `@opentelemetry/sdk-trace-base@2.0.0` pin `@opentelemetry/core` to exactly `2.0.0`, but the bundle ships `core@2.8.0`.

npm's dependency resolver (Arborist) therefore wants a nested `core@2.0.0`. A real install extracts the bundle as-is and never writes that entry, so the lockfile keeps flipping between states and `npm ci` rejects whichever one it gets.

- Versions 1.17.0 and 1.17.3 have clean bundles; 1.17.4, 1.17.6, 1.17.7 and 1.17.8 are broken.
- A lockfile made with `--package-lock-only` is also missing bundle entries that a real install records (the `toolkit-lib` errors).

## Things that did not work

- **Scoped overrides of `resources` / `sdk-trace-base`** (earlier commit a489cd7, since reverted). npm can't override bundled packages. That lockfile only passed because it happened to contain the nested `core@2.0.0` entries, and the next `npm install` removed them.
- **Overriding `@opentelemetry/core` under data-construct.** npm got stuck in an endless `placeDep ... REPLACE` loop and crashed.

## Fix applied (commit 4b331e6)

1. **`package.json`:** added `"@aws-amplify/data-construct": "1.17.3"` to `overrides`. This pins the whole package (not something inside its bundle), which npm handles normally. It also brings in `graphql-api-construct@1.21.3`, whose bundle is clean.
2. **`package-lock.json`:** regenerated. It is stable across repeated `npm install` runs.
3. **`amplify.yml`:** every phase (backend, frontend preBuild/build, test preTest) now uses `nvm install 24` / `nvm use 24` instead of Node 17.9.1, so builds run npm 11. This matches `.nvmrc` (v24.21.0). react-router 7 and Cypress 15 need Node 20 or later anyway.

## Verification

- A clean `npm ci --ignore-scripts` from the new lockfile in an empty directory installed 2861 packages.
- `npm ci --dry-run` passes on npm 11.21.2 and fails on 8.11.0 and 10.9.4 (`type-fest`), which is why the Node 24 change is needed.
- `@aws-amplify/backend-data@1.9.0` loads with data-construct 1.17.3, and `npx tsc --noEmit -p amplify` passes.
- **Not verified:** an actual Amplify deploy (`ampx pipeline-deploy` / sandbox).

## Other findings

- `~/.npmrc` contains `allow-scripts=@aws-amplify/cli`. npm 11.19+ treats that as a CLI flag and fails project installs with `EALLOWSCRIPTS` ("--allow-scripts is not allowed in project-scoped installs"). Note that `npx` passes the user config down to the npm it launches.
- `npm ls` reports `invalid: type-fest@0.8.1`. It comes from react-scripts' `@pmmmwh/react-refresh-webpack-plugin` optional peer, existed before this work, and is harmless on npm 11.

## Files in this directory

- `handoff.md`: state and next steps
- `bug-report.md`: short upstream bug report for aws-amplify/amplify-backend
- `check-bundle.js`: script that lists dependency mismatches inside an extracted package bundle
