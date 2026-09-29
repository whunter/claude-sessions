# Handoff: stack drift and `amplify gen2-migration lock` (dlp-access, env `gentwo`)

Repo: `~/dev/dlp/access/dlp-access`, branch `whunter/upgrade/amplify-gen-2`. No git commits this session: the only change is in `amplify/`, which is gitignored. The pre-existing uncommitted changes in `src/graphql/*` were left alone.

## Next step

Run lock interactively and confirm the prompt:
```
amplify gen2-migration lock
```
As of the end of this session it passes validation. **Do not `amplify push` or redeploy from the Amplify console before running it.** Something after the last push rewrote the S3 API template without the override (see below), and that could bring the drift back.

What lock will do:
- Set `DeletionPolicy` / `UpdateReplacePolicy: Retain` on the DynamoDB tables (Archive, Collection, Collectionmap, History, MetadataField, PageContent, Partner, Site) and on the Cognito resources, and turn on DynamoDB deletion protection.
- Block `amplify push` on `vtdlp-dev/gentwo`, and block migrating any other env until this one is finished or rolled back.
- It can be undone with `amplify gen2-migration lock --rollback`.

## State to know about

- **`amplify/backend/api/vtdlp/override.ts`** sets the default API key's `expires` to `now + 90 days`, rounded down to the hour. AppSync truncates to the hour, so without the rounding every deploy shows up as CFN drift.
  - The override must use `(resources.api as any).GraphQLAPIDefaultApiKeyDefaultApiKey`. The typed name `GraphQLAPIDefaultApiKey` doesn't exist at runtime.
  - `cli-inputs.json` / `backend-config.json` still say `apiKeyExpirationDays: 7`. The override replaces that, but the CLI's default path still uses 7.
  - The file is gitignored. It lives only locally and in `#current-cloud-backend.zip` in the deployment bucket.
- **Deployed API key** `da2-illj6uqhhvdjbkszy6jdg5m6wm` expires `1798452000` (2026-12-28 10:00 UTC).
- **S3 API template** `s3://amplify-vtdlpdev-gentwo-c4fb8-deployment/amplify-cfn-templates/api/cloudformation-template.json` was replaced by hand with the local staged template, which is identical to the deployed nested stack. The stale version is backed up at `/tmp/api-template.stale.json` (the bucket has no versioning) and can be deleted.
- **Unexplained:** after the push deployed at about 10:51 UTC, the S3 API template was rewritten at 10:53:00 with a 7-day expiry, not rounded and without the override. The deployed stack was not changed. It could be a second transform pass inside `amplify push`, or a console/branch build. If template drift comes back after any future push, compare that S3 object with `aws cloudformation get-template` on the API nested stack and re-upload the staged template.

## Debugging tips from this session

- Override `console.log` output and thrown error messages are not shown (`InvalidOverrideError: Executing overrides failed.` only). To inspect, write values into a resource's metadata, e.g. `resources.opensearch.OpenSearchDomain.addMetadata("DBG", …)`, run `amplify build`, and grep the built stack.
- `amplify api gql-compile` skips overrides; use `amplify build`.
- Lock's drift detection has two kinds of check: resource drift (deployed resource vs template) and template drift (S3 template vs deployed template, done with a change set).
