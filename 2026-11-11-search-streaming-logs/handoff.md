# Hand-off: OpenSearch streaming alerts and recovery (dlp-access-next-cdk)

## State

- Branch `whunter/feature/add/search-streaming-logs`, head `b90c599`. **Not pushed**
  (no upstream). Working tree clean.
- All four tickets in `docs/infra/opensearch-stream-recovery/issues/` are
  implemented. Each is marked "done (awaiting on-AWS verification)". The
  "Verified on a feature environment" box is unchecked on every ticket.
- Tests pass: `cd infra && npx tsc --noEmit -p . && npm test && npm run test:lambda`
  (159 Jest, 77 pytest).
- Nothing has been deployed.

## Commits (after the tickets commit `5865c67`)

- `eb8bf7c` Alert on failed OpenSearch streaming batches
- `da6d463` prettier (whitespace-only, unrelated files split out)
- `1176af5` Resync OpenSearch documents by ID
- `1916fb0` Resync a whole table into OpenSearch with paging
- `b90c599` Document the failed-batch recovery procedure

## Open decision: code-review findings awaiting the user's go-ahead

Recommended fixes (not yet applied):

1. **`resync.py` `_parse`:** a non-string `model` (e.g. `["Archive"]`) raises
   `TypeError: unhashable type`. Check `isinstance(model, str)` first and add a
   test case.
2. **Resync sends `INSERT`:** the stream's `MODIFY` path also deletes the legacy
   Amplify `id=<id>` document. Switch resync's synthetic records to `MODIFY` so
   a resync cleans that up too. Update the tests' expected bulk lines.
3. **Runbook by-ID invoke:** add `--cli-read-timeout 0`. Without it, a long run
   trips the CLI's 60s timeout and the CLI retries, invoking the function again.
4. **`alertEmails`:** the ticket said optional, but it is required and set to
   `[]` everywhere. Make it `alertEmails?:` and default to `[]` in the stack.
5. Standards nits worth doing:
   - share the streaming and resync OpenSearch grants in `api-stack.ts`;
   - expose a public entry point instead of calling `streaming._lambda_handler`;
   - rename `RESERVE_MS`, and the tuple-returning `_parse`.

Lower priority: a test fixture for the repeated 230-item table, and extracting
the alerting block out of the `ApiStack` constructor.

## Next steps

1. Get the user's answer on the fixes above, apply them with TDD at the agreed
   seams (synthesized template, and `resync.lambda_handler` with faked DynamoDB
   and `post_data_to_opensearch`), and commit.
2. Deploy to a feature env (`f-<slug>`) and run each ticket's on-AWS check:
   - send a test SQS message → alarm ALARM → purge → OK;
   - hand-edit a doc → resync by ID;
   - full-table `processed` equals the item count;
   - walk the runbook end to end on a deliberately failed batch.
3. Ask before pushing, then reply to the reviewer, pointing at
   `docs/opensearch-streaming.md`.
4. When a team or list address exists, add it to `alertEmails` for
   `pre-production` and `production`.
