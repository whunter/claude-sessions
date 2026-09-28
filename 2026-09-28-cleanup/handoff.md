# Handoff: admin removal and dependency cleanup (dlp-access)

Repo: `~/dev/dlp/access/dlp-access`, branch `whunter/upgrade/amplify-gen-2`. The working tree is clean and HEAD is `052c313`. **The branch has no upstream and has never been pushed**, so everything below exists only locally. It sits on top of `217ad21` ("Migrate Amplify JS from v5 to v6"), which is also on no remote. Its parents `8a878fe` and `b5d5428` are on `origin/wlh_mirador_update`. The branch point from `main` is `e5e3939`. No PR is open.

## Commits this session (`git log 217ad21..HEAD`)

- `5718f48` Remove admin section. This is a cherry-pick of `35dc682` from `whunter-refactor-remove-admin`.
- `ad85a69` Remove code and packages orphaned by admin removal.
- `c7e941a` Remove unused npm packages (20 packages).
- `1f9417d` Consolidate semantic-ui-css on the GitHub version.
- `485760a` Remove react-3d-viewer and the OBJ/MTL viewers.
- `2e6d751` Remove unused imports from ArchivePage.
- `2fe1a25` Fix remaining eslint warnings, including the BabylonElement disposal bug.
- `052c313` Remove unused FeaturedItems Controls component and its tests.

The commit messages carry the per-item reasoning. `summary.md` in this folder has the narrative.

## State to know about

- **Discarded upgrade commits:** `8be0255` (patch and minor) and `46d5b50` (majors with TypeScript 5) were reset away. They are reachable only through `git reflog` and will expire eventually. The findings from them are in `summary.md`, section 1.
- **Lost pre-session changes:** before this session, the working tree held uncommitted changes of the user's own: a "latest everything" `package.json` and a deleted `package-lock.json`. The reset did not restore them. Backups were written to the session scratchpad at `/private/tmp/claude-502/-Users-whunter-dev-dlp-access-dlp-access/683c356e-0fdb-4e57-864b-03f750118fbe/scratchpad/` (`uncommitted-package-json.diff` and `package.json.working`). Both files were still there when this was written, but `/private/tmp` is cleared on reboot.
- **Git hooks:** husky 3 is back in charge of the hooks; `core.hooksPath` is unset. The lint-staged config still has a `git add` step, which lint-staged 13 warns about on every commit. The warning is harmless.
- **Local run:** `REACT_APP_REP_TYPE` is required. With `Default` or `demo`, the app stays on "Loading" locally, both before and after these changes, which is probably missing site data in the backend. So nothing has been smoke-tested in a browser. At minimum, check a GLTF (Babylon) archive page, because the engine is now disposed on unmount.
- **Left in place on purpose:**
  - `src/ui-components/`, `src/aws-exports.js` and `src/schema.js` are untracked, gitignored Amplify output that nothing imports.
  - `src/graphql/mutations.js` is now unused, but it is tracked codegen output.
  - `Editor.scss` still styles Quill-authored HTML on public pages.
  - `@emotion/*`, `@mui/system`, `i18next` and `react-i18next` stay as Mirador and MUI peers.
  - `mocha` and `mochawesome` stay for the Cypress reporter.
- **semantic-ui-css:** the lockfile resolves it as `git+ssh://git@github.com/...`. That predates this session. If a CI box without GitHub SSH access fails to install, look there first.
- **Rotate the leaked password:** `CYPRESS_password=access2020` was removed from `examples/amplify.yml` but remains in git history. If the `devtest` Cognito user still exists, rotate its password or delete the user.

## Suggested next steps

1. Push the branch and open a PR, or decide whether the admin removal should go to `main` separately. `whunter-refactor-remove-admin` already exists for that.
2. Retry the dependency upgrade on this slimmer tree. Known constraints:
   - TypeScript >= 5 needs the react-scripts `overrides` trick.
   - Mirador 4.x pins MUI 7 and `react-i18next` <= 15 or 17.
   - `@mui/x-tree-view` 9 needs the `SyntheticEvent | null` handler signature in `SubCollectionsTree.tsx` and `useLoadMap.ts`.
   - React 19 is still blocked by `semantic-ui-react` 2.x (`findDOMNode`) and by `react-leaflet` 5 requiring React 19.
3. Consider replacing `semantic-ui-react`. It is now used only by `Pagination`, `SortOrderDropdown`, `FilterDropdown` and `CollectionsListView`, and it is the main React 19 blocker.
4. Fix or delete the stale unit tests: 16 of 19 suites fail.
