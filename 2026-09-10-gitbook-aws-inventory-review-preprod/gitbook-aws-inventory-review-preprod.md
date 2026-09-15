# GitBook "Lambda inventory pre-prod" — AWS Resource Cross-Check

Source: GitBook page *Lambda inventory pre-prod* (VTUL-DLP space, change request #20 "Restore original Lambda flow layout")
https://app.gitbook.com/o/TvFOuK5Ys0OrTXXA3B6X/s/1wMf6kajAYFiqHU5KNPP/~/edit/~/changes/20/elastic-beanstalk-and-cdk-implementation-timeline/lambda-inventory-pre-prod

Checked against **account 226388486048** (`arn:aws:iam::226388486048:user/vtdlp-whunter-workload`, local CLI profile `eb-cli`) — the page itself names `CFN stack: amplify-vtdlpdev-vtdlppprd-1ccb6` and `Environment: PreProd (vtdlppprd)`; that stack was confirmed to exist only in this account (it does not exist in the other configured account, 196766403141, which is production). This is the reverse pairing from the "Lambda inventory prod" review: here, 226388486048 is the target account, and 196766403141 is the *other* account.

Verification method: `aws cloudformation describe-stacks` / `list-stack-resources` (recursively through nested stacks), `aws lambda list-functions` (this IAM user **does** have `lambda:ListFunctions` in this account, unlike in the prod account — so the Lambda side of this check is a real enumeration, not name-by-name spot checks), `aws amplify get-app`/`get-branch`, `aws cognito-idp describe-user-pool`, `aws s3api head-bucket`. `appsync:GetGraphqlApi` was denied for this user, so the AppSync API was confirmed indirectly via its CloudFormation resource entry instead.

## Important difference from the "Lambda inventory prod" page

The prod page named ~30 exact Lambda/API/stack identifiers directly (readable off tables/diagrams via screenshot). **This page does not** — it names only a handful of literal identifiers (Amplify app, AppSync API, CFN stack) and otherwise describes Lambda functions with short **descriptive labels** in a bucket table ("OpenSearch indexer", "feedback", "robots.txt", "sitemap.xml", "2020 ARK", "deploy helper", "S3 trigger", "swva ingest", "nodejs12 fn") rather than function names. Where I paired a label to an actual Lambda function name below, that pairing is **inferred** from CloudFormation stack membership, runtime version, naming, or creation date — not read directly off the page — and is flagged as such. Treat List 2/3 entries for these labels as best-effort matches, not literal confirmations.

---

## List 1 — Every AWS resource/identifier named on the page

**Literal identifiers**
- Amplify app: `vtdlp-pprd` (`d3reyduta3lkkz`)
- Amplify branch: `federated-pprd` → `federated-pprd.dlp.cloud.lib.vt.edu`
- AppSync API: `vtdlp-vtdlppprd` (`77eik3yv7rbdbjhjemas6h7dmi`)
- CFN stack: `amplify-vtdlpdev-vtdlppprd-1ccb6`
- Asana task reference (not an AWS resource): `app.asana.com/.../task/1211598488142567`

**Lambda bucket labels (descriptive, not literal names)** — page states "PREPROD — 117 functions in the account, 10 named for pprd"
- Bucket A (Keep → CDK), count 1: "OpenSearch indexer" (5,075 runs)
- Bucket B (Keep + wire AppSync), count 0 (EMPTY — page states no AppSync Lambda data sources exist)
- Bucket C (fold into Next.js), count "1 + 2 new": "feedback", "robots.txt", "sitemap.xml"
- Bucket D (delete), count 5: "2020 ARK", "deploy helper", "S3 trigger", "swva ingest", "nodejs12 fn"

---

## List 2 — Confirmed to exist in account 226388486048

**Literal identifiers — all confirmed**
- Amplify app `vtdlp-pprd` (`d3reyduta3lkkz`) — confirmed via `amplify get-app`, default domain `d3reyduta3lkkz.amplifyapp.com`
- Amplify branch `federated-pprd` — confirmed via `amplify get-branch` (stage: PRODUCTION)
- CFN root stack `amplify-vtdlpdev-vtdlppprd-1ccb6` — confirmed (`UPDATE_COMPLETE`), plus its 4 direct nested stacks (`apivtdlp`, `authvtdlpdeve943a1f8`, `functionS3Triggerf2aaed76`, `storageenvassets`) and their children
- AppSync API `77eik3yv7rbdbjhjemas6h7dmi` — confirmed indirectly as an `AWS::AppSync::GraphQLApi` resource inside the `apivtdlp` nested stack (direct `appsync:GetGraphqlApi` call was denied)
- Cognito User Pool `us-east-1_uRznIAeDB` (`vtdlpdeve943a1f8_userpool_e943a1f8-vtdlppprd`) — confirmed via `cognito-idp describe-user-pool`
- S3 bucket `vtdlpdev-env-assets1ccb6-vtdlppprd` (env assets) — confirmed via `head-bucket`
- S3 bucket `amplify-vtdlpdev-vtdlppprd-1ccb6-deployment` (Amplify deployment bucket) — confirmed via `head-bucket`

**Bucket A — "OpenSearch indexer" → matched with high confidence**
- `amplify-vtdlpdev-vtdlpppr-OpenSearchStreamingLambd-fA6oVGORD8If` — found inside the `SearchableStack` nested stack under the same `apivtdlp` stack, wired to 3 `AWS::Lambda::EventSourceMapping`s (DynamoDB streams) and an `OpenSearchDataSource`, which matches the page's "indexer, 5,075 runs" description structurally.

**Bucket B — confirmed EMPTY as the page states**
- Reviewed all `AWS::AppSync::DataSource` resources under the `apivtdlp` stack tree: only `NONE_DS` and `OpenSearchDataSource` exist — no `AWS_LAMBDA`-type data source. This matches the page's claim that no AppSync Lambda data sources exist.

**Bucket D — 5 labels, matched with varying confidence (all via `lambda list-functions`, a real account-wide enumeration)**
- "S3 trigger" → `S3Triggerf2aaed76-vtdlppprd` — **high confidence**: it's the `LambdaFunction` resource inside the `functionS3Triggerf2aaed76` nested stack that hangs directly off the root CFN stack.
- "swva ingest" → `S3toDDB-pprd-swva-s3toddb-feTPZPVOcIqw` — **high confidence**: name literally contains `pprd` + `swva`.
- "nodejs12 fn" → `amplify-dlpdev-pprd-102439-au-UserPoolClientLambda-sJEN0qLxsQf2` — **high confidence**: it is the only function in the entire 119-function account running `nodejs12.x` (all other legacy functions are `nodejs18.x`/`20.x`/`22.x`), and its name is pprd-tagged.
- "deploy helper" → `amplify-vtdlpdev-vtdlpppr-UpdateRolesWithIDPFuncti-jyCwaxeHKkfu` — **medium confidence**: this is an Amplify auth post-deploy custom resource (invoked once via a CloudFormation `Custom::LambdaCallout` during stack deploys to sync IDP roles), which fits "deploy helper" functionally, but the page never uses this name.
- "2020 ARK" → `vtdlp_resser_urlredirection` and/or `vtdlp_resser_urlcreation` — **medium confidence**: both exist in this account, both are the hand-deployed ARK/resolution-service Lambdas, and both carry a `2020-01-27` creation date matching the "2020" label. Could not disambiguate whether the page's single "2020 ARK" line item means one of these or both together.

**Named-for-pprd Lambda functions not covered by any bucket in this page** (found via full `lambda list-functions`; likely the "10 named for pprd" count includes these even though the page's bucket table doesn't mention them — consistent with how the prod page also covered only a subset of that account's resources)
- `dlp-pprd-services-Resolutio-NameResolutionFunction-DCDC67EZNSGt`
- `dlp-pprd-services-MintServiceApp-KC-UpdateFunction-k7qAHHHrjLJn`
- `dlp-pprd-services-MintServiceApp-KCXJ-NoidFunction-YDFPhZxOi98J`

Together with the OpenSearch indexer and the 5 Bucket D items (counting the two `vtdlp_resser_*` functions separately), this totals exactly **10** functions whose names or CFN placement tie them to `pprd`/`vtdlppprd` — matching the page's own count. This 10-count match is corroborating evidence for the label pairings above, not independent proof of each individual pairing.

---

## List 3 — Named/described on the page but NOT found (or not nameable) in account 226388486048

- Bucket C's "feedback", "robots.txt", "sitemap.xml" — no Lambda function anywhere in the account's full 119-function list has a name containing `feedback`, `robot`, or `sitemap` (checked via substring search across `lambda list-functions` output, case-insensitive). The page itself frames these as mostly **not yet existing** ("1 + 2 new" — 2 of the 3 are explicitly new), and the 1 existing one could not be identified by name; it isn't one of the 10 pprd-tagged functions found by any of the matches above, so it may run under a name with no obvious keyword match, or it may be a page-writer's forward-looking placeholder.

### Notes / caveats
- Unlike the prod-page review, this account's IAM user **has** `lambda:ListFunctions`, so the Lambda side of this check is an actual enumeration (119 functions reviewed) rather than name-by-name lookups — the "not found" call for the Bucket C labels is stronger than the equivalent calls in the prod review.
- `appsync:GetGraphqlApi` and (untested but likely, by analogy with the prod account) direct `apigateway:GET` are not available to this IAM user in this account; anything AppSync-related was confirmed via CloudFormation resource listings instead of the AppSync API directly.
- Every Bucket A/D pairing above is an inference from naming/runtime/CFN-membership, not a literal name read off the page — re-verify with whoever wrote the GitBook page if these pairings are used for anything higher-stakes than this review (e.g., before deleting any Bucket D function).
