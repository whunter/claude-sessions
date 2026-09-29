# Handoff: Gen 2 migration after Step 4 (dlp-access)

Repo: `~/dev/dlp/access/dlp-access`, branch `gen2-main`. The Step 4 changes are committed locally in `4b9f620` and **not pushed**. See `summary.md` for the diff rationale.

## Next steps (guide Step 5 onward)

1. `git push origin gen2-main`.
2. In the Amplify console, go to App Settings → Branch Settings → Add Branch → `gen2-main`, and deploy. The build uses `amplify.yml` (backend `ampx pipeline-deploy`, then the CRA build).
3. After the deploy, generate local outputs for dev:
   `npx ampx generate outputs --app-id <gen2-appId> --branch gen2-main --out-dir src`.
   Until this exists, `npm start` fails because `src/amplify_outputs.json` is missing. The file is gitignored (`amplify_outputs*`).
4. **Step 6:** functional testing on the Gen 2 URL: sign-in, data CRUD (admin/editor groups), S3 upload and download, search queries (custom VTL resolvers), and the feedback form.
5. **Step 7:** refactor. Check out a Gen 1 branch, `amplify pull --appId <appId> --envName gentwo`, then `amplify gen2-migration refactor --to amplify-<appId>-gen2main-branch-<suffix>`.
6. **Step 8:** uncomment `postRefactor();` in `amplify/backend.ts`, then commit and push (Step 9). Skipping this causes downtime. `postRefactor` renames the storage bucket to the Gen 1 name `vtdlpdev-env-assetsc4fb8-gentwo`.

## Watch out for

- **API key expiry regression:** the generated `amplify/data/resource.ts` has `apiKeyAuthorizationMode: { expiresInDays: 7 }`. In Gen 1, the `override.ts` from the 2026-09-29-stack-drift session set 90 days, rounded down to the hour. Consider changing Gen 2 to a longer expiry, or the public site's API key will lapse after a week.
- **Node in the build:** the `amplify.yml` frontend phases pin `nvm use 17.9.1`. The backend phase doesn't pin a version and relies on the image default, and ampx needs Node 18 or later. If the backend build fails on the Node version, add `nvm use 20` to the backend phase.
- **Lambda deps / circular dependencies:** the guide's troubleshooting section covers merged function deps in the root `package.json`, and circular nested-stack dependencies. Neither has been seen yet.
- The Gen 1 table names all end in `-gentwo` (API id `b7anxcwcargyxfsgq4vtrtdbem`). `branchName` in the mapping must match the Hosting branch (`gen2-main`). For `npx ampx sandbox`, set it to `'sandbox'` temporarily to share the tables.
- Leftover Gen 1 files `src/amplifyconfiguration.json` and `src/aws-exports.js` still exist locally (gitignored). Nothing imports them now.
