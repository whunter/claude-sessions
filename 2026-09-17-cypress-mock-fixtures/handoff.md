# Handoff — cypress-mock-fixtures (2026-09-17)

## Context
`access/dlp-access` repo, branch `whunter-refactor-update-tests`. Full
narrative in `session-summary.md`.

This session builds directly on top of two earlier same-day sessions on
this branch:
- `../2026-09-17-cypress-test-refactor/` — rewrote specs to match current
  site behavior/data, but still hit the **live** AppSync API directly.
- `../2026-09-17-cypress-node-upgrade/` — bumped Cypress 13.6.4 → 15.21.1.

This session's goal: stop the suite from depending on the live,
changing database at all. Everything now replays captured GraphQL
responses bundled in the repo.

**Nothing from this session is committed yet** — working tree has the
mocking infrastructure plus edits to every integration spec, all
unstaged, per this repo's "only commit when explicitly asked" convention.

## State (uncommitted)
```
 M .gitignore
 M cypress.config.ts
 M cypress/e2e/api/search_archives_graphql.cy.js
 M cypress/e2e/integration/*.cy.js               (all 15, mockGraphQL wired in)
 M cypress/support/commands.js
 M cypress/support/e2e.js
?? cypress/fixtures/graphql/                      (captures/ + datasets/, ~756KB)
?? cypress/support/localSearchArchives.js
```

## Next steps
1. If asked to finish this up: `git add` the files above (including the
   new `cypress/fixtures/graphql/` and `cypress/support/localSearchArchives.js`)
   and commit (normal message, no attribution per this user's CLAUDE.md),
   then ask before pushing.
2. Full suite is currently green: **41/41 integration passing, 5/5 API
   passing, 0 skipped.**
3. **Known, unfixed app bug** (not a test issue): the archive detail page
   404s ("Page Not Found") for any archive whose `heirarchy_path` has more
   than one level (i.e. it's nested more than one collection deep).
   Verified directly against the live dev server across 6+ different
   records, all from different collections. Confirmed NOT a data problem
   — the GraphQL lookups the page performs both return the item correctly;
   something in the client-side routing/rendering path chokes on the
   deeper nesting. Worth a look by whoever owns the archive detail page
   route/component. The test suite now deliberately avoids these records
   rather than working around the bug.
4. Fixture captures (`cypress/fixtures/graphql/captures/*.json`) are a
   point-in-time snapshot of the live Amplify environment as of this
   session. Re-run the capture pass (see below) whenever the underlying
   data changes enough that specs should reflect it, or when a spec is
   added/changed and needs a new operation captured.

## How to run

### Full suite (this is now the standard way to run tests — no live
backend or AWS login required):
```
npm run start-dlp &
npx cypress run --spec "cypress/e2e/integration/**/*.cy.js" --headless --browser electron
CYPRESS_API_TEST_ONLY=true npx cypress run --spec "cypress/e2e/api/**/*.cy.js" --headless --browser electron
```
(`search_archives_graphql.cy.js`, the only spec under `api/`, is now a
pure local unit test against a bundled dataset — it needs no server and
no network at all, but is kept isolated behind `CYPRESS_API_TEST_ONLY` so
it can run without `baseUrl` being reachable.)

### Refreshing the captured fixtures (only needed when live data drifts
or a new query needs capturing — requires a real login + live dev server,
same as the old workflow):
```
npm run start-dlp &
CYPRESS_capture=true npx cypress run --spec "cypress/e2e/integration/**/*.cy.js" --headless --browser electron
```
This overwrites/extends `cypress/fixtures/graphql/captures/*.json` with
fresh request/response pairs recorded from the live API. Commit the
resulting fixture diffs like any other change.

## CI
**No CI test job exists for Cypress in this repo yet** — the only GitHub
Actions workflows (`pr.yml`, `merge.yml`) trigger Amplify Console preview
deploys, not test runs. If/when a CI job is added:
- No new packages need to be installed beyond what's already in
  `devDependencies` (`cypress`, `cypress-localstorage-commands`) and
  `dependencies` (`cypress-file-upload`) — this refactor added zero new
  npm packages, only new fixture/support files.
- On a bare Linux CI image, Cypress needs its native OS dependencies
  (`libgtk2.0-0`, `libgtk-3-0`, `libnotify-dev`, `libgconf-2-4`,
  `libnss3`, `libxss1`, `libasound2`, `libxtst6`, `xauth`, `xvfb`) —
  these are what the official `cypress-io/github-action` (or
  `cypress/base` Docker image) installs for you, so prefer that action
  over hand-rolling `npx cypress run` in a raw `ubuntu-latest` job.
- The app under test must be served before Cypress runs — e.g.
  `cypress-io/github-action`'s `start` + `wait-on` inputs pointed at
  `npm run start-dlp` and `http://localhost:3000`.
- No AWS credentials, `amplify` CLI, or live backend access are needed in
  CI at all now — that's the whole point of this refactor.

## Key facts for a fresh agent
- `cy.intercept()` only catches **browser-driven** requests. The one spec
  that used `cy.request()` (Node-side, bypasses intercept) —
  `search_archives_graphql.cy.js` — was rewritten as a local unit test
  instead (see `cypress/support/localSearchArchives.js`), since
  `searchArchives` is `@searchable`/OpenSearch-backed and `amplify mock
  api` doesn't support that locally either.
- `cy.task()` cannot be called from inside a `cy.intercept()` req/res
  callback (throws a Cypress command-queue error). Captures are buffered
  in a plain JS array in the callback and flushed via `cy.task()` from a
  normal `afterEach` instead.
- Replay matching is by GraphQL operation name (regex-extracted from the
  query string) + exact-JSON-match on request variables. Unmatched
  requests get a warning + an empty `{ data: {} }` rather than failing
  hard, to help spot fixture gaps quickly.
- Media assets (IIIF/Mirador images, PDFs, glTF models) referenced by
  mocked GraphQL responses still resolve to real S3/CDN URLs — those were
  intentionally left un-mocked as out of scope for a "no live DB" fix.
  Flag this to the user if it ever needs to change.

## Suggested skills
- No special skill needed to commit/push the pending changes — normal git
  workflow.
- **`code-review`** (medium/high effort) is worth running on the diff
  before committing, given its size (18 files + a new fixtures directory).
- Any future CI-wiring work should probably just look at how
  `cypress-io/github-action`'s README recommends structuring the job,
  rather than hand-building the Linux dependency list above.
