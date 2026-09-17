# Session Summary — cypress-mock-fixtures (2026-09-17)

## Task
`access/dlp-access` is hosted via AWS Amplify v1, hybrid CLI-managed.
Its Cypress suite hit the live GraphQL/AppSync API directly, so tests
would break whenever the underlying database data changed — independent
of any actual app regression. The task: refactor the suite to run
against mocked data bundled in the repo instead.

This picks up right after two earlier same-day sessions on the same
branch (`whunter-refactor-update-tests`) — a full spec rewrite to match
current site behavior/data (`../2026-09-17-cypress-test-refactor/`) and a
Cypress 13→15 upgrade (`../2026-09-17-cypress-node-upgrade/`). Both of
those still queried the live backend; this session removes that
dependency entirely.

## Approach chosen
Presented with three options, the user picked **cy.intercept + captured
live data**: run the app against a real dev server once, record every
GraphQL request/response pair via `cy.intercept`, save them as fixture
files bundled in the repo, then replay those fixtures in all future runs.
This keeps fixtures realistic (real production-shaped data) without any
live dependency thereafter.

## What was built

### Capture / replay infrastructure
- **`cypress.config.ts`**: two new Node-side tasks (`setupNodeEvents`) —
  `captureGraphQL` (append/dedupe request+response pairs into per-operation
  JSON files under `cypress/fixtures/graphql/captures/`) and
  `loadGraphQLCaptures` (read them all back into one map for replay).
- **`cypress/support/commands.js`**:
  - `cy.captureGraphQLTraffic()` / `cy.flushCapturedGraphQL()` — active
    only under `CYPRESS_capture=true`, used for the one-time recording
    pass against a live, logged-in dev server.
  - `cy.mockGraphQL(overrides?)` — the command every spec now calls
    before `cy.visit(...)`. Intercepts `POST **/graphql`, matches each
    request to a captured fixture by operation name (regex-parsed from
    the query string) + exact JSON-equality on variables, and replays
    the captured response. Falls back to a warning + `{ data: {} }` for
    anything uncaptured, so gaps are loud, not silent hangs.
  - Removed the now-dead `graphqlRequest` command (only the API spec used
    it, and that spec no longer touches the network at all).
- **`cypress/support/e2e.js`**: wires the capture hooks in under
  `CYPRESS_capture=true`; otherwise specs call `cy.mockGraphQL()`
  themselves (kept per-spec rather than one global intercept, so a
  spec's own response overrides don't have to coexist with a second,
  competing intercept registered elsewhere).

### The one spec that couldn't use interception at all
`cypress/e2e/api/search_archives_graphql.cy.js` used to call the live
AppSync API directly via `cy.request()` — which runs Node-side in the
Cypress process, not through the browser, so `cy.intercept()` can't touch
it. The user asked whether `amplify mock api` could stand in for a local
backend here instead; research confirmed it does **not** support
`@searchable` (OpenSearch-backed) resolvers, and `searchArchives` (along
with virtually every other query in this app) is `@searchable`. That
ruled out a local Amplify mock entirely.

Instead, this spec is now a fully local, no-network unit test:
- **`cypress/support/localSearchArchives.js`** — a hand-written
  reimplementation of the resolver's sort/tie-break/pagination contract,
  reverse-engineered from real `nextToken` values captured off the live
  API (format: `${sortFieldValue}::key::${custom_key}`, implying a
  secondary sort by `custom_key` ascending, with null-valued sort fields
  sorting last regardless of direction).
- **`cypress/fixtures/graphql/datasets/brouwer_collection_archives.json`**
  — 64 real archive records (Charlie Brouwer Collection) fetched directly
  from the live API, used as the dataset this local function sorts/pages
  over. All test assertions were computed from this real data.

### Every integration spec (15 files)
Added `cy.mockGraphQL()` immediately before each `cy.visit(...)`. Two
specs needed more than a straight replay:
- `searchfacet_checkbox.cy.js` / `show_all_less_buttons.cy.js` used to
  mutate a live passthrough response on the fly (via `req.continue`) to
  inject a synthetic "medium" facet for testing. Rewritten to load the
  captured `SiteBySiteId` fixture via `cy.fixture()`, mutate it in JS,
  and pass it as an override to `cy.mockGraphQL({ SiteBySiteId: [...] })`.

### Data-drift fixes (found once mocking made the data static/inspectable)
The Amplify environment changed mid-session (user switched environments
before the live capture pass), so a few assertions needed updating to
match current reality — none of these are related to the mocking work
itself:
- `browse_collections.cy.js`: root-collection count 11 → 10.
- `search_bar.cy.js`: "Additions" search 63 → 4 results; "certificate"
  search 20 → 23 results.

### A real app bug, found and deliberately not "fixed" by hacking the test
`language_config.cy.js`'s second test clicks the first English-language
archive search result and checks its metadata. Whatever record happened
to sort first kept 404'ing ("Page Not Found"). Investigation (see below)
showed this reproduces against the live API too — it's not a mocking
artifact, and not a data-availability problem (both of the archive
page's own lookups return the item correctly). It correlates with
`heirarchy_path` depth: **every** record checked whose hierarchy had more
than one level 404'd; a 1-level record worked fine.

Rather than leave that flaky/broken record wired into a captured fixture,
the user asked to swap it out for a different, working archive record.
That was done by:
1. Testing ~6 different English-language archives directly against the
   live dev server (`localhost:3000`) to confirm the pattern and find a
   working, 1-level-hierarchy candidate:
   `ark:/53696/7m260s54` ("Salem Fire Aide Jailed in Miami..." — Salem
   Fire & EMS Department), verified to render correctly with
   `Language: en` displayed.
2. Fetching that record's full live GraphQL data (matching every field
   the app's `SearchArchives`/`GetCollection` queries actually select)
   and splicing it into the captured fixtures: replacing the broken
   record as the first item in the English-archive-listing capture, plus
   adding the archive detail page's two-step lookup queries, its parent
   collection (`GetCollection`), and its "related items" sidebar query —
   all four fetched live and appended to
   `cypress/fixtures/graphql/captures/{SearchArchives,GetCollection}.json`.
3. Un-skipping the test (it had been `it.skip`'d earlier in this session
   while the bug was still being triaged) — it now passes.

The underlying app bug (nested-hierarchy archives 404) is real, was
reproduced live, and is **not fixed** — flagged in the handoff for
whoever owns that page.

## Verification
Final clean-slate run:
```
npx cypress run --spec "cypress/e2e/integration/**/*.cy.js" --headless --browser electron
→ 41 passing, 0 failing, 0 skipped

CYPRESS_API_TEST_ONLY=true npx cypress run --spec "cypress/e2e/api/**/*.cy.js" --headless --browser electron
→ 5 passing, 0 failing
```
Zero live network/database dependency for either suite. (Media asset
URLs — images, PDFs, 3D models — embedded in the mocked metadata still
point at real CDN/S3 hosts; that was treated as out of scope for a
"stop depending on the live DB" task, not yet explicitly confirmed with
the user as a permanent decision.)

## Open items for the user
1. Nothing has been committed or pushed — awaiting explicit go-ahead.
2. The nested-`heirarchy_path` 404 bug is real and unfixed; worth routing
   to whoever owns the archive detail page.
3. Confirm the media-asset-mocking scope decision (leaving real CDN/S3
   URLs live) is acceptable long-term, or whether those should eventually
   be mocked/stubbed too.
