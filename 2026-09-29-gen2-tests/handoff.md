# Handoff — gen2-tests (2026-09-29)

## Context
Repo `access/dlp-access`, branch `gen2-tests` (from the Gen 2 migration
line). Full narrative in `session-summary.md`.

Builds on `../2026-09-17-cypress-mock-fixtures/`, which did the
offline-Cypress work on `whunter-refactor-update-tests`. That work came
*before* the Amplify Gen 2 migration. This session ported it onto the
Gen 2 code, merged `main`, and fixed the Jest suite.

## State
All work is committed on `gen2-tests`. **None of it is pushed.**

```
ab5d515 Update collection page Jest tests to match current components
7fb1ad3 Update home page and Thumbnail Jest tests to match current components
238d919 Merge branch 'main' into gen2-tests
587f8ee Refactor Cypress suite to replay captured GraphQL data instead of live API
526b3f8 Ignore Cypress-generated artifacts
41df18a Refactor Cypress suite to match current site behavior and data
30c8f93 Add cypress/tsconfig.json to fix Cypress ts-node compilation
```

Untracked `amplify-backup/` is left as it was; it is not from this session.

## Test status
| Suite | Result |
|---|---|
| Cypress integration | 41/41 passing |
| Cypress API (offline) | 5/5 passing |
| Jest | 19/19 suites, 77/77 tests passing |

## Next steps
1. Push `gen2-tests` and open a PR when ready. Ask the user before pushing.
2. When live data drifts, re-record the Cypress fixtures (commands below).
3. There is still no CI job that runs either test suite. See the CI notes
   in `../2026-09-17-cypress-mock-fixtures/handoff.md`.
4. A known app bug is not fixed: archive pages 404 when `heirarchy_path`
   has more than one level. It was documented in the 09-17 session, and
   the tests avoid those records.

## How to run
The app needs `src/amplify_outputs.json`. CRA only imports from inside
`src/`, so copy it from the repo root if it's missing:
```
cp amplify_outputs.json src/
```

**Jest:**
```
CI=true npx react-scripts test --watchAll=false
```

**Cypress:** no backend or AWS login is needed. `start-dlp` sets
`REACT_APP_REP_TYPE=federated`, which the fixture variables depend on.
```
npm run start-dlp &
npx cypress run --spec "cypress/e2e/integration/**/*.cy.js" --headless --browser electron
CYPRESS_API_TEST_ONLY=true npx cypress run --spec "cypress/e2e/api/**/*.cy.js" --headless --browser electron
```

**Re-record the Cypress fixtures from the live API:**
```
CYPRESS_capture=true npx cypress run --spec "cypress/e2e/integration/**/*.cy.js" --headless --browser electron
```

## Key facts for a fresh agent
- **How Cypress mocking works:**
  - `cy.mockGraphQL()` in `cypress/support/commands.js` intercepts
    `POST **/graphql`. It matches recordings by operation name and exact
    variables.
  - A request with no recording gets `{ data: {} }` and a console warning.
    It never falls through to the live API.
- **What stays live:** media (IIIF, PDF, glTF) still loads from the real
  S3/CDN. This is deliberate.
- **`commands.js` history:** the old Amplify v5 `Auth`/`signIn` and
  `aws-exports` code was removed. The Gen 2 app uses Amplify JS v6.
- **Jest mocks:**
  - Jest never touches the network. Tests spy on `FunctionalFileGetter.getFile`
    and on `fetchTools` functions, using data from `src/fixtures/mock_*.ts`.
  - Don't mutate shared fixtures in tests. One test did that to `mock_site`
    and has been fixed.
- **Role conventions for current components:**
  - Decorative images have `alt=""`, so query them with the role
    `presentation`, not `img`.
  - Native selects have the role `combobox`. The Subject filter is still a
    custom `listbox`.
- **Stale caches after a merge:** if the dev server shows ESLint "JSON
  parse `<<<<<<<`" errors, clear these caches under `node_modules/.cache`:
  `.eslintcache`, `eslint-webpack-plugin` and `default-development`.
