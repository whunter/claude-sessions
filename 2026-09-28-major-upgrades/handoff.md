# Handoff: major-version dependency upgrades (dlp-access)

Repo: `~/dev/dlp/access/dlp-access`, branch `whunter/upgrade/amplify-gen-2`. The working tree is clean and HEAD is `3d2d273`. **The branch has still never been pushed** (see the cleanup session handoff, `../2026-09-28-cleanup/handoff.md`). No PR is open.

## Commits this session (`git log 9a3d315..HEAD`)

- `675b0c0` TypeScript 4.9 → 6.0.3, i18next 23 → 26, react-i18next 15 → 17.
- `93dd074` FontAwesome 6 → 7, react-fontawesome 0.2 → 3, @mui/x-tree-view 7 → 9, html-react-parser 3 → 6, query-string 8 → 9, react-share 4 → 5, react-ga4 2 → 3, react-slick 0.29 → 0.31, slick-carousel 1 → 2.
- `7a5d348` react-router-dom 6 → 7.
- `8e223b9` Babylon.js 7 → 9.
- `ee10ca3` @testing-library/react 14 → 16 (with @testing-library/dom 10), jest-dom 5 → 7, @types/jest 29 → 30, @types/node 18 → 24, plus Jest 27 compatibility config.
- `3d2d273` cypress 13 → 15, mocha 10 → 11, mochawesome 7 → 8, prettier 2 → 3, lint-staged 13 → 16, husky 3 → 9.

## State to know about

- **TypeScript override:** react-scripts 5 peer-depends on `typescript ^3.2.1 || ^4`. `package.json` has `"overrides": {"react-scripts": {"typescript": "$typescript"}}`. `tsconfig.json` already had `"ignoreDeprecations": "6.0"`, which TS 6 needs for `moduleResolution: node` and `baseUrl`.
- **Jest 27 shims** (react-scripts' Jest ignores package `exports` and its jsdom lacks some globals):
  - `package.json` `jest.moduleNameMapper` maps `react-router/dom` and `entities/decode|escape` to their CJS files.
  - `jest.transformIgnorePatterns` now also transforms the ESM-only htmlparser2 family (`html-react-parser`, `html-dom-parser`, `htmlparser2`, `domhandler`, `domutils`, `domelementtype`, `dom-serializer`, `entities`).
  - New `src/setupTests.js` polyfills `TextEncoder`/`TextDecoder` (react-router 7) and `structuredClone`.
  - If another upgrade adds a "Cannot find module 'x/y'" or "Cannot use import statement" failure, extend these lists.
- **Husky 9:** hooks live in `.husky/pre-commit` (`npx lint-staged`) and are installed by the new `prepare` script, which sets `core.hooksPath=.husky/_`. The old husky 3 hooks in `.git/hooks` were deleted. Fresh clones get hooks on `npm install`.
- **Node version:** `.nvmrc` is 24. The user's shell runs Node 20.17, which gives EBADENGINE warnings: jest-dom 7 and sanitize-html 2.17.7 want ≥ 22, and sass, htmlparser2 and others want ≥ 20.19. Everything still works on 20.17 today.
- **`examples/amplify.yml` installs Node 17.6.0** for both build and test. If the real Amplify console build spec matches, deploys will fail. This needs checking and updating to 24.
- **Prettier 3** reports 22 files under `src` as unformatted. They were not reformatted; lint-staged only formats staged files.
- **`npm outdated` quirk:** it showed `jest-dom`, `sass` and `sanitize-html` as newer than `latest`. Per-version `npm view` confirmed the installed versions *are* `latest` and not deprecated; the outdated output used stale cached tags.

## Held back, with reasons

- **TypeScript 7:** the npm package is the Go-native compiler. Its main export is only `version` and there is no stable JS compiler API. `fork-ts-checker-webpack-plugin` and `@typescript-eslint` 5 (inside react-scripts) require one, so 6.x is the ceiling while on CRA.
- **@mui/material / @mui/system 9:** Mirador 4.2.4 peers are `^7`.
- **React 19, @types/react(-dom) 19, react-leaflet 5:** blocked by `semantic-ui-react` 2.x (`findDOMNode`). It is used only in `Pagination.js`, `SortOrderDropdown.js`, `FilterDropdown.js` and `CollectionsListView.tsx`. react-leaflet 5 requires React 19.
- **@types/node 26:** kept at 24 on purpose to match `.nvmrc`.
- **react-scripts:** 5.0.1 is the final release. Moving to Vite (or similar) would lift the TS 7 and Jest 27 limits.

## Verification

- `npx tsc --noEmit` passes. `REACT_APP_REP_TYPE=Default CI=true npm run build` compiles with no warnings; this was checked after every commit.
- Unit tests: all 19 suites now run. 53 of 72 tests pass; before this session only 3 suites loaded (25 tests). The 19 failures are identical to the pre-upgrade commit run with the same Jest shims. They are stale role/markup assertions.
- Five tests (`collection-items`, `collections-list-view`, `collection-top-content`, `featured-static-image`, `thumbnail`) now query `presentation` instead of `img`. testing-library/dom 10 follows ARIA: `<img alt="">` is decorative.
- `npx cypress verify` passes. Cypress specs were **not** run.
- **No browser smoke test** (the local app still sticks on "Loading"). Priorities: a Babylon (GLTF) archive page, the collection sub-collection tree (x-tree-view 9), FontAwesome icons (v7 glyph changes), social share buttons and the related-items carousel.

## Suggested next steps

1. Fix the Node version in the Amplify build spec (17.6 → 24) and use Node 24 locally (`nvm use`).
2. Smoke-test in a browser once site data loads, especially the items listed above.
3. Push the branch and open a PR (not yet done; ask first).
4. Replace `semantic-ui-react` in the four files, then upgrade to React 19 and react-leaflet 5.
5. Fix or delete the 19 stale unit tests.
6. Optionally run `prettier --write` over `src` in a separate formatting-only commit.
7. Longer term: migrate off react-scripts to unlock TypeScript 7 and a modern Jest/Vitest.
