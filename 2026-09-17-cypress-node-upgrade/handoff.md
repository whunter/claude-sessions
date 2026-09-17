# Handoff — cypress-node-upgrade (2026-09-17)

## Context
`access/dlp-access` repo, branch `whunter-refactor-update-tests`. Full
narrative in `summary.md` in this directory. Prior, related session (the
Cypress test-suite rewrite this branch started with) is in
`../2026-09-17-cypress-test-refactor/`.

Latest commits (all local, **not pushed**):
```
92b7bff Ignore Cypress-generated artifacts
c6266c2 Upgrade Cypress from 13.6.4 to 15.21.1
80fd95d Refactor Cypress suite to match current site behavior and data
ec8e008 Add cypress/tsconfig.json to fix Cypress ts-node compilation
```

## State
Working tree clean. Nothing pending to commit from this session.

## Next steps (if picked back up)
1. **If asked to push**: ask before pushing, per this repo's convention
   (this session only committed, did not push).
2. **If asked to pursue Cypress 16.x**: it's a real migration, not a
   version bump — `Cypress.env()` was removed (breaks
   `cypress/support/commands.js`'s `cy.signIn`, which calls
   `Cypress.env("password")`) and the Electron test browser is deprecated.
   Needs Node ≥22 (already confirmed working on this machine via `nvm use
   22.23.2`). Migrate call sites to `cy.env()`/`Cypress.expose()`, pick a
   replacement browser, then re-run the full suite to verify.
3. **If asked to pin a Node version**: no `.nvmrc` or `package.json`
   `engines` field exists yet. Node 22 (Active LTS, "Jod") is confirmed
   working; 24 (LTS, "Krypton") was spot-checked but not fully verified
   against the test suite.
4. **If picking up general Cypress work**: see `summary.md` here and the
   prior session's docs for full context on what test coverage looks like
   now and why.

## How to run / verify
1. Start the app against the real AppSync backend (production backend,
   no local backend needed):
   ```
   BROWSER=none REACT_APP_REP_TYPE=federated REACT_APP_GIT_COMMIT=$(git rev-parse HEAD) npm run start-dlp
   ```
2. Run Cypress headless (Node ≥20.1 required; 22 recommended and
   confirmed working — use `nvm use 22.23.2` if testing a non-default
   Node version, without changing this machine's global default):
   ```
   npx cypress run --browser electron
   ```
   (The `TS_NODE_PROJECT=cypress/tsconfig.json` workaround from the
   Cypress 13 era is no longer required with 15.x, but is harmless to
   still pass if used out of habit.)
3. For `cypress/e2e/api/search_archives_graphql.cy.js` specifically, also
   export (see `src/aws-exports.js` for the real values — not reproduced
   here):
   ```
   CYPRESS_apiUrl="<aws_appsync_graphqlEndpoint>"
   CYPRESS_apiKey="<aws_appsync_apiKey>"
   ```

## Key facts for a fresh agent
- The repo's `npm install --force` requirement is caused by an unrelated
  `@babylonjs/core`/`@babylonjs/gui` peer-dependency mismatch, not Cypress.
  It will still be needed regardless of any future Cypress/Node changes
  unless that babylon version conflict is separately resolved.
- Cypress has no peer dependencies, so its version is otherwise decoupled
  from the rest of the dependency tree.

## Suggested skills
- No special skill needed to continue committing/pushing — normal git
  workflow.
- **`code-review`** (medium effort) if the next session wants a second
  pass on the `package.json`/`package-lock.json`/`.gitignore` diffs before
  pushing.
- No skill needed for the Cypress 16 migration if picked up — it's plain
  test-code editing plus re-running the suite to verify, same approach
  used throughout this and the prior session.
