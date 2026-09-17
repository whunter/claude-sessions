# Session Summary — cypress-node-upgrade (2026-09-17)

## Goal
Follow-on to the same-day `2026-09-17-cypress-test-refactor` session (see that
directory for the full test-rewrite narrative). Question this time: can
Cypress be upgraded, and how far can Node be upgraded, in
`access/dlp-access`, without breaking the build?

## Approach
Rather than just reading changelogs, actually performed each upgrade in the
working tree, reinstalled dependencies, built the app, and ran the full
Cypress suite to verify, then decided what to keep based on real results.

## Cypress upgrade: 13.6.4 → 15.21.1
- First established that this repo's pre-existing need for `npm install
  --force` is a peer-dependency conflict between `@babylonjs/core@7.x` and
  `@babylonjs/gui@8.x` (via `react-babylonjs`) — **entirely unrelated to
  Cypress**. Cypress itself has no peer dependencies, so upgrading it
  doesn't interact with that conflict at all; `--force` is required either
  way, before or after.
- Bumped to the latest 15.x (15.21.1). `npm install --force` resolved
  cleanly, `npm run build` succeeded, and the full 47-test suite passed.
- As a side effect, confirmed the `cypress/tsconfig.json` /
  `TS_NODE_PROJECT` workaround (added in the prior session, commit
  `ec8e008`, to work around Cypress 13's older bundled ts-node choking on
  the root `tsconfig.json`'s `"ignoreDeprecations": "6.0"`) is **no longer
  needed** with 15.x's newer bundled ts-node. Left in place since removing
  it wasn't asked for and it's harmless.
- **Tried Cypress 16.1.0 and rejected it.** It requires Node ≥22 (fine,
  see below), but more importantly it's a real breaking API change, not
  just a version bump: `Cypress.env()` was removed (this repo's
  `cypress/support/commands.js` `cy.signIn` helper reads
  `Cypress.env("password")`), and the Electron test browser is deprecated.
  All 16 spec files failed immediately with `Cypress.env() was removed in
  Cypress version 16.0.0`. Migrating to 16 would need real test-code
  changes (switch to `cy.env()`/`Cypress.expose()`, pick a non-Electron
  browser) — out of scope for "can we upgrade," reverted to 15.x.

## Node upgrade: how far
Current global/default Node on this machine is `20.17.0` (unchanged —
tested other versions via `nvm use` in-session only, nothing changed
system-wide). `nvm` is installed with several other versions available.
- Cypress 13→15.x all declare support for Node ≥20 (`^16 || ^18 || >=20`
  through `^20.1.0 || ^22 || >=24`), so no Node bump was strictly required
  for the 15.x upgrade itself.
- **Node 22.23.2 (Active LTS, "Jod")** — fully verified: clean install,
  successful build, and the full 47-test Cypress suite passing.
- **Node 24.21.0 (LTS, "Krypton")** — spot-checked install + build only
  (both succeeded); not run through the full test suite, since the user
  directed standardizing on 22 once confirmed it's the current LTS.
- No `.nvmrc` or `package.json` `engines` field was added — if the team
  wants to formally pin a Node version for dev/CI, that's a separate,
  not-yet-made decision.

## Result
Two new commits on `whunter-refactor-update-tests` (stacked on the prior
session's `ec8e008`/`80fd95d`):
- `c6266c2` — "Upgrade Cypress from 13.6.4 to 15.21.1"
  (`package.json`/`package-lock.json`)
- `92b7bff` — "Ignore Cypress-generated artifacts" (added
  `cypress/screenshots/`, `cypress/videos/`, `cypress/downloads/` to
  `.gitignore`, after noticing a stray `cypress/screenshots/` directory
  left over from a failed Cypress-16 test run)

Working tree clean as of end of session. Branch has not been pushed to
remote (per this repo's convention — push only on explicit request).

## Open items, not done this session
- Cypress 16.x migration (`Cypress.env()` → `cy.env()`, drop Electron) —
  deferred, real follow-up work if wanted.
- No `engines`/`.nvmrc` Node pin added.
- The `/collection/8n449w6w` 404 bug surfaced in the prior session is
  still unfixed and unrelated to this session's work.
