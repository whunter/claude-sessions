# Session summary: major-version upgrades (2026-09-28)

Repo: `~/dev/dlp/access/dlp-access` (the CRA React front end), branch `whunter/upgrade/amplify-gen-2`.

## Goal

Following the cleanup session's handoff, upgrade major versions in `package.json` as far as can be done safely. The top priority was TypeScript ≥ 5, then every other package.

## Approach

- Upgrade in related groups.
- After each group, run `tsc --noEmit` and a `CI=true` production build, fix anything that broke, and commit.
- Check peer dependencies (`npm view <pkg>@<major> peerDependencies engines`) up front to find hard blockers.

## What happened

### 1. TypeScript 6 and i18n (`675b0c0`)
- Went to TypeScript 6.0.3 instead of 5, since TS 6 is still the JS-based compiler.
- react-scripts' `typescript ^3 || ^4` peer is bypassed with an npm override.
- The existing `ignoreDeprecations: "6.0"` in `tsconfig.json` covered the deprecated options.
- The TS pin had held i18next back. With it lifted, i18next went to 26 and react-i18next to 17, which is within Mirador's allowed `^17`.

### 2. Runtime libraries (`93dd074`)
- Upgraded FontAwesome, x-tree-view, html-react-parser, query-string, react-share, react-ga4, react-slick and slick-carousel.
- The only code change: x-tree-view 9's `onExpandedItemsChange` passes `SyntheticEvent | null`. `SubCollectionsTree.tsx` and `useLoadMap.ts` were updated.

### 3. react-router 7 (`7a5d348`)
- No code changes. All routes are absolute and no data-router APIs are used.

### 4. Babylon.js 9 (`8e223b9`)
- No code changes. Only long-standing core and GUI APIs are used.

### 5. Testing libraries and types (`ee10ca3`)
- The first test run looked unchanged (3 of 19 suites passing), but that hid the problem: most suites could not load at all.
- Causes, all from Jest 27 in react-scripts:
  - No package `exports` support (`react-router/dom`, `entities/decode`).
  - ESM-only `domhandler` and friends from html-react-parser 6.
  - Missing jsdom globals (`TextEncoder`, `structuredClone`).
- Fixed with `moduleNameMapper`, `transformIgnorePatterns` and a new `src/setupTests.js`.
- To isolate what the upgrade itself changed, the previous commit was checked out in a temporary worktree and run with the same shims (19 failures).
- The upgraded tree had 5 extra failures, all from testing-library/dom 10 treating `<img alt="">` as `presentation`. Those test queries were updated. The failing set then matched the previous commit exactly.

### 6. Dev tooling (`3d2d273`)
- Upgraded Cypress to 15 (the support code uses no removed APIs; `cypress verify` passes), mocha 11 and mochawesome 8.
- Upgraded Prettier to 3. The `.prettierrc.json` trailingComma setting keeps the formatting style.
- Upgraded lint-staged to 16 and removed the obsolete `git add` step.
- Migrated husky 3 to 9: `.husky/pre-commit` and a `prepare` script, with the old husky 3 hooks removed. The new hook ran on the commit.

### 7. Investigated and left alone
- **TypeScript 7:** the Go port has no stable JS API, which react-scripts' checker and linter need.
- **MUI 9:** Mirador pins 7.
- **React 19 and react-leaflet 5:** semantic-ui-react blocks them.
- **@types/node:** stays at 24 to match `.nvmrc`.
- **The `npm outdated` "newer than latest" oddity:** caused by stale cached tags, not pulled releases.

## Verification

- Type check and production build pass after every commit.
- Unit tests: 19/19 suites load and 53/72 tests pass (before: 3 suites, 25 tests). The remaining failures are the existing stale tests.
- Cypress was verified but no specs were run. There was no browser smoke test, because the local app still sticks on "Loading".

## Open issues

- `examples/amplify.yml` uses Node 17.6. The local shell runs Node 20.17, while `.nvmrc` says 24.
- Prettier 3 flags 22 unformatted files.
- The branch is still unpushed.
