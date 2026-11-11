# Session summary: OpenSearch streaming failure alerts and recovery

- Date: 2026-11-11
- Repo: dlp-access-next-cdk
- Branch: `whunter/feature/add/search-streaming-logs`

## Goal

Answer the review comment: "it would be nice to document the notification setup
and the retry/recover procedure for failed opensearch stream batches." The user
asked how people are alerted to OpenSearch streaming failures.

## Finding

Nobody was alerted. The DynamoDB stream event source mapping retries 3 times
with batch bisection, then sends a failure record to the `OpenSearchStreamingFailures`
SQS queue (14-day retention). Nothing alarmed on that queue. Those records hold
only stream pointers (shard and sequence range). The stream keeps data for 24h,
so recovery has to re-read the table. No reindex or backfill tooling existed.

## Decisions (grilling session)

- Add alerting in this PR:
  - an SNS topic per environment, with its ARN as a stack output;
  - an `alertEmails` setting in environment config, empty everywhere for now
    (use team addresses, not personal ones);
  - an alarm at queue visible messages >= 1 over 5 min, missing data not
    breaching, sending ALARM and OK to the topic;
  - no Lambda `Errors` alarm.
- Recovery is a resync Lambda in the streaming code asset:
  - it wraps items as synthetic stream records and runs them through the existing
    handler, so documents are indexed identically;
  - payload `{model, ids?, startKey?}`;
  - by ID: IDs missing from the table are deleted from the index;
  - full table: stops at ~12 min and returns `{processed, lastEvaluatedKey}`
    for the operator to resume;
  - no orphan sweep.
- Race with the live stream: document it ("run at a quiet time, rerun if in
  doubt"). No locking or external versioning.
- The runbook lives in a new `docs/opensearch-streaming.md`, linked from the
  README and `docs/deployment.md`.

## What was done

1. Wrote four tickets to `docs/infra/opensearch-stream-recovery/issues/`
   (01 alerting, 02 resync by ID, 03 full-table paging, 04 runbook).
2. Implemented them test-first at two agreed seams: CDK template assertions,
   and pytest on `resync.lambda_handler` with faked DynamoDB and OpenSearch post.
   - **Alerting:** SNS topic, alarm and email subscriptions in `api-stack.ts`;
     `alertEmails` in `environments.ts`.
   - **Resync:** `infra/lambda/opensearch-streaming/resync.py`, deployed as
     `dlp-access-next-<env>-opensearch-resync`.
     - Permissions: `BatchGetItem`/`Scan` on Archive/Collection only, plus the
       streaming function's OpenSearch grants.
     - Batches of 100, deduplicated IDs, retries of unprocessed keys, a time
       budget, and payload validation.
   - **Runbook:** how streaming works, alerting and subscribing, the five-step
     alarm-to-OK procedure (with the SQS message format, a Logs Insights query
     and common causes), the resync reference and limitations.
3. Moved prettier's unrelated whitespace fixes into their own commit.
4. Ran a two-axis code review (standards and spec) with parallel sub-agents.

## Outcome

- Five commits on the branch, not pushed.
- All tests pass.
- Review findings are summarized in `handoff.md` and wait on the user's
  go-ahead.
- The on-AWS verification of each ticket is still to do.
