# Hand-off: gitbook-aws-inventory-review-preprod

**Deliverable:** `gitbook-aws-inventory-review-preprod.md` (this directory) — the three-list AWS resource cross-check for the pre-prod GitBook page, same format as the earlier prod-page review.
**Source doc:** GitBook page "Lambda inventory pre-prod" (VTUL-DLP space, change request #20 "Restore original Lambda flow layout")
https://app.gitbook.com/o/TvFOuK5Ys0OrTXXA3B6X/s/1wMf6kajAYFiqHU5KNPP/~/edit/~/changes/20/elastic-beanstalk-and-cdk-implementation-timeline/lambda-inventory-pre-prod
**Prior session this repeats the process from:** `../2026-09-01-gitbook-aws-inventory-review/` (the "Lambda inventory prod" page review)

## What's done

The task is complete. `gitbook-aws-inventory-review-preprod.md` contains:

1. **List 1** — every AWS identifier/label named on the page (literal names: Amplify app, branch, AppSync API, CFN stack; plus the Lambda "bucket" descriptive labels the page uses instead of function names).
2. **List 2** — the subset confirmed to exist in account 226388486048, including best-effort Lambda-label-to-function-name pairings with confidence levels noted.
3. **List 3** — labels that could not be matched to any existing resource (the "feedback"/"robots.txt"/"sitemap.xml" Bucket C items).

## How the check was done

- Read the page via GitBook's Editor view (`get_page_text` + screenshots) — unlike the prod page, this one rendered as normal readable text/tables, no OCR risk.
- The page names `CFN stack: amplify-vtdlpdev-vtdlppprd-1ccb6` and `Environment: PreProd (vtdlppprd)`. That stack does **not** exist in the default AWS CLI credentials (account 196766403141, which the prior session identified as production) — it only exists under the local `eb-cli` profile (account 226388486048). So **this review's target account is the reverse of the prior one**: 226388486048 is "the account" here, 196766403141 is the other one.
- Walked the CFN stack tree recursively (`list-stack-resources` on the root and every nested stack) to enumerate real resources: Amplify auth/API/storage sub-stacks, the AppSync GraphQL API, the `SearchableStack` (OpenSearch indexer Lambda + data source), and the standalone `functionS3Triggerf2aaed76` stack.
- This IAM user **has** `lambda:ListFunctions` in this account (unlike in the prod account), so I pulled the full 119-function list and grep'd it for keyword/runtime/name matches to the page's descriptive Lambda labels ("OpenSearch indexer", "2020 ARK", "deploy helper", "S3 trigger", "swva ingest", "nodejs12 fn", "feedback", "robots.txt", "sitemap.xml").
- Confirmed the Amplify app/branch via `amplify get-app`/`get-branch`, the Cognito user pool via `cognito-idp describe-user-pool`, and two S3 buckets via `head-bucket`. `appsync:GetGraphqlApi` was denied, so the AppSync API was confirmed only via its CFN resource entry.

## What's NOT done / caveats to flag if this comes up again

1. **This page doesn't give literal Lambda function names**, unlike the prod page. Every Bucket A/D label-to-function pairing in List 2 is an *inference* (from CFN membership, runtime version, naming pattern, or creation date), not a literal read off the page — I flagged each with a confidence level (high/medium). Don't treat these as page-confirmed identifiers, especially the "deploy helper" and "2020 ARK" pairings (medium confidence) — re-verify with whoever wrote the page before acting on them (e.g., before deleting any Bucket D function).
2. **Bucket C ("feedback", "robots.txt", "sitemap.xml") came back unmatched.** No Lambda in the account's full 119-function list contains any of those keywords. The page itself says 2 of the 3 are new/not-yet-built, and I couldn't identify the 1 claimed-existing one by name — it may run under a name with no obvious keyword tie, or the page's count may be forward-looking.
3. **The "10 named for pprd" corroboration is aggregate, not per-item.** I found exactly 10 pprd-tagged/associated Lambda functions across Bucket A + Bucket D (counting both `vtdlp_resser_*` functions as the "2020 ARK" pair) + 3 `dlp-pprd-services-*` functions the bucket table doesn't mention at all. The count matching the page's stated "10" is good aggregate evidence the overall inference approach is on track, but it does not independently confirm any single pairing.
4. **`appsync:GetGraphqlApi` and (by analogy with the prod account) likely `apigateway:GET`** are not available to this IAM user in account 226388486048 — nothing AppSync-specific (schema, resolvers, data source configs beyond what CFN lists) was queried directly.

## Key files

- `gitbook-aws-inventory-review-preprod.md` — the actual deliverable (three lists + methodology + caveats section at the bottom).
