# Session Summary: gitbook-aws-inventory-review-preprod

**Date:** 2026-09-10
**Goal:** Repeat the AWS-resource cross-check process from the 2026-09-01 "Lambda inventory prod" GitBook review, this time against the companion "Lambda inventory pre-prod" page.

## What happened

1. Located the prior session's hand-off (`../2026-09-01-gitbook-aws-inventory-review/handoff.md`) to recover the methodology: read the GitBook page fully, extract every named AWS resource, then verify each against AWS via CLI, producing three lists (named-on-page / confirmed-exists / confirmed-not-found).
2. Opened the target GitBook page (`lambda-inventory-pre-prod`) in the Editor view. Unlike the prod page, it rendered as normal readable text — no screenshot/OCR step was needed.
3. Read the page content: it documents a "PreProd (vtdlppprd)" environment tied to Amplify app `vtdlp-pprd` (`d3reyduta3lkkz`), AppSync API `77eik3yv7rbdbjhjemas6h7dmi`, and CFN stack `amplify-vtdlpdev-vtdlppprd-1ccb6`. Its core content is a "bucket" table categorizing ~10 Lambda functions by disposition (Keep→CDK / Keep+wire / fold into Next.js / Delete), using short descriptive labels ("OpenSearch indexer", "2020 ARK", "S3 trigger", etc.) instead of literal function names.
4. Checked both configured AWS CLI credentials (default = account 196766403141, profile `eb-cli` = account 226388486048) against the CFN stack name from the page. It only exists in 226388486048 — establishing that this review's target account is the *reverse* of the prior session's (which targeted 196766403141 as "production").
5. Walked the CFN stack tree recursively via `list-stack-resources` on the root stack and all nested stacks (auth, API/AppSync incl. `SearchableStack`, storage, and the standalone S3-trigger function stack) to enumerate real resources.
6. Ran `aws lambda list-functions` against account 226388486048 (this IAM user has `ListFunctions` there, unlike in the prod account) — got a full 119-function list and matched it against the page's descriptive labels using keyword/runtime/naming/date heuristics, flagging each match's confidence.
7. Confirmed the Amplify app/branch, Cognito user pool, and two S3 buckets directly via their respective `describe`/`get`/`head-bucket` calls. AppSync API access was denied directly, so it was confirmed only via CloudFormation.
8. Wrote the three-list deliverable to `gitbook-aws-inventory-review-preprod.md`, explicitly flagging the key methodological difference from the prior review: this page requires *inferring* Lambda identities from descriptive labels rather than reading literal names, so List 2/3 entries are confidence-graded rather than flatly confirmed.

## Key takeaways / non-obvious findings

- **Account pairing is reversed from the prior review.** The GitBook space covers two environments across two AWS accounts; which account is "the target" depends entirely on which CFN stack name the specific page under review references — always re-derive this per page rather than assuming.
- **Not all GitBook inventory pages give literal resource names.** The prod page had exact names; this pre-prod page uses descriptive shorthand instead, requiring inference-based matching. Any future page in this space should be checked for which style it uses before assuming the prior methodology transfers 1:1.
- **The page's own "10 named for pprd" count was useful corroborating evidence** — 10 independently-found pprd-associated Lambda functions matched that count exactly, lending confidence to the overall matching approach even though individual pairings (especially "deploy helper" and "2020 ARK") remain inferred, not literal.
- Three Lambda labels ("feedback", "robots.txt", "sitemap.xml") had no matching function anywhere in the account by keyword search — consistent with the page's own framing that most of these are new/not-yet-built.

## Follow-ups if this thread continues

- If someone needs to act on the Bucket D "delete" list, get explicit confirmation on the "deploy helper" and "2020 ARK" pairings from whoever authored the page — those are the two medium-confidence inferences.
- If `lambda:ListFunctions`/`appsync:GetGraphqlApi` access is ever granted for the *other* account (196766403141) or denied is lifted for AppSync in 226388486048, re-run affected checks for a stronger positive/negative confirmation.
