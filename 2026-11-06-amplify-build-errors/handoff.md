# Hand-off: npm ci lockfile sync failure (gen-2-dlp-access, `light-env-gen2`)

## State

- Fixed and committed as **4b331e6** on `light-env-gen2`. **Not pushed.**
- The commit changes `package.json` (override `@aws-amplify/data-construct` to `1.17.3`), `package-lock.json` (regenerated) and `amplify.yml` (Node 17.9.1 → Node 24 in every phase).
- A clean local `npm ci` works. No Amplify deploy has been run with this change.
- The working tree is clean. The previous uncommitted lockfile was discarded; a temporary copy existed only in the session scratchpad.

## Suggested next steps

1. **Push and run an Amplify branch build.** Confirm that:
   - `nvm install 24` works in the build image
   - the backend phase's `npm ci` and `ampx pipeline-deploy` succeed
   - the frontend `npm ci --force` / `npm run build` succeed
2. **Check that pinning data-construct to 1.17.3 is safe.** `backend-data@1.9.0` declares `^1.17.7`, so 1.17.3 is outside its range. Typecheck and loading pass, but compare the synthesized data stack or do a sandbox deploy, and watch for missing data/AI features added in 1.17.4–1.17.8.
3. **Submit `bug-report.md`** to https://github.com/aws-amplify/amplify-backend/issues (the data-construct package is published from the amplify-category-api repo, so that repo may fit better).
4. **Remove the override** once a data-construct newer than 1.17.8 ships with a consistent bundle. To check a new version:
   ```sh
   npm pack @aws-amplify/data-construct@<ver> && mkdir x && tar xzf aws-amplify-data-construct-<ver>.tgz -C x
   node check-bundle.js "$PWD/x/package/node_modules" <path-to>/node_modules/semver
   ```
   Then drop the override, run `npm install` twice and confirm `npm ci` passes.
5. **Optional:** remove `allow-scripts=@aws-amplify/cli` from `~/.npmrc`, or move it into package.json `allowScripts`. On npm 11.19+ it causes `EALLOWSCRIPTS`.

## Notes

- After pulling a lockfile change, run `rm -rf node_modules && npm ci`, not `npm install`. If `node_modules` is left over from the old layout, `npm install` rewrites the lockfile around it (data-construct ends up hoisted) and `npm ci` fails again on missing `@aws-cdk/toolkit-lib`, `@smithy/*` and other entries. This happened once after the fix; restoring the committed lockfile and reinstalling cleanly resolved it.
- Always regenerate the lockfile with a full `npm install` on npm 11, not with `--package-lock-only` and not with npm 8 or 10. Lock-only mode leaves out bundle entries, and older npm versions disagree on the optional-peer `type-fest`.
- Don't try to override packages inside the Amplify bundles. It has no effect (a489cd7) or sends npm into an endless loop (overriding `@opentelemetry/core`).
- When testing npm behaviour, set `npm_config_userconfig` to an empty file. Otherwise `~/.npmrc`'s `allow-scripts` hides the real error.
