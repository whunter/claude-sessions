# Handoff — cypress-test-refactor (2026-09-17)

## Context
`access/dlp-access` repo, branch `whunter-refactor-update-tests`. Full
narrative in `session-summary.md`.

Latest commit: `ec8e008` — "Add cypress/tsconfig.json to fix Cypress
ts-node compilation" (**not pushed**).

**14 spec files rewritten + 1 deleted are still unstaged** in the working
tree (not committed) — waiting on explicit instruction to commit, per this
repo's "only commit when asked" convention:

```
 M cypress/e2e/api/search_archives_graphql.cy.js
 M cypress/e2e/integration/additional_pages.cy.js
 M cypress/e2e/integration/archive_media_views.cy.js
 M cypress/e2e/integration/archive_metadata_display.cy.js
 M cypress/e2e/integration/browse_collections.cy.js
 M cypress/e2e/integration/collection_metadata_display.cy.js
 D cypress/e2e/integration/derivative_download_section.cy.js
 M cypress/e2e/integration/language_config.cy.js
 M cypress/e2e/integration/linked_metadata.cy.js
 M cypress/e2e/integration/related_items.cy.js
 M cypress/e2e/integration/search_bar.cy.js
 M cypress/e2e/integration/search_facet.cy.js
 M cypress/e2e/integration/searchfacet_checkbox.cy.js
 M cypress/e2e/integration/show_all_less_buttons.cy.js
 M cypress/e2e/integration/view_options.cy.js
```
Untouched (already matched current site behavior):
`category_select_checkbox.cy.js`, `richSchemaTools.cy.js`.

## Next steps
1. If asked to finish this up: `git add` the files above and commit
   (normal message, no attribution per this user's CLAUDE.md), then ask
   before pushing.
2. If picking back up to verify or extend: see "How to run" below — the
   whole suite passed 47/47 as of this session, but the live backend's data
   changes over time, so re-verify before trusting old results.
3. One real (possibly app-level, not test-level) issue was surfaced but
   **not fixed**, since it was out of scope for a test-only task: visiting
   `/collection/8n449w6w` ("Taubman Museum of Art") directly, or via the
   breadcrumb link from one of its own archive items, renders "Page Not
   Found". Worth a look by whoever owns `CollectionsShowPage.tsx` /
   `useGetCollection`.

## How to run / verify
1. Start the app against the real AppSync backend (no local backend
   needed — `src/aws-exports.js` already points at production, and AWS
   creds are available in this environment):
   ```
   BROWSER=none REACT_APP_REP_TYPE=federated REACT_APP_GIT_COMMIT=$(git rev-parse HEAD) npm run start-dlp
   ```
2. Run Cypress headless (note the required `TS_NODE_PROJECT` — see below):
   ```
   TS_NODE_PROJECT=cypress/tsconfig.json npx cypress run --spec <glob> --browser electron
   ```
3. For `cypress/e2e/api/search_archives_graphql.cy.js` specifically, also
   export (values from `src/aws-exports.js`, not secret beyond normal
   API-key-scoped read access):
   ```
   CYPRESS_apiUrl="https://ff4jrkonzrduziosmblcybfw4u.appsync-api.us-east-1.amazonaws.com/graphql"
   CYPRESS_apiKey="<aws_appsync_apiKey from src/aws-exports.js>"
   ```
   No CI wiring exists for Cypress in this repo — it's run manually.

## Key facts for a fresh agent
- **Cypress couldn't even boot before this session** — Cypress 13's bundled
  `ts-node` chokes on the root `tsconfig.json`'s
  `"ignoreDeprecations": "6.0"`. Fixed via `cypress/tsconfig.json`
  (committed, `ec8e008`) + always passing `TS_NODE_PROJECT=cypress/tsconfig.json`.
- The site's data, markup, and feature set have all drifted significantly
  since these tests were last accurate — see `session-summary.md` for the
  full list of UI/behavior changes discovered (metadata card markup,
  reduced search facets, no more field-specific search, native `<select>`
  page-size dropdown, dead `DownloadLinks` feature, etc.) and the real
  item/collection IDs now hardcoded into the specs.

## Suggested skills
- No special skill needed to just commit/push the pending changes — normal
  git workflow.
- **`code-review`** (medium/high effort) if the next session wants a
  second pass on the diff before committing.
- No skill needed to investigate the `/collection/8n449w6w` 404 — that's
  plain app debugging, not test work, if someone picks it up.
