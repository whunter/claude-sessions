# GitBook "Lambda inventory prod" — AWS Resource Cross-Check

Source: GitBook page *Lambda inventory prod* (VTUL-DLP space, change request #20 "Restore original Lambda flow layout")
https://app.gitbook.com/o/TvFOuK5Ys0OrTXXA3B6X/s/1wMf6kajAYFiqHU5KNPP/~/edit/~/changes/20/elastic-beanstalk-and-cdk-implementation-timeline/lambda-inventory-prod

Checked against the AWS account currently authenticated in this session:
- **Account 196766403141** (`arn:aws:iam::196766403141:user/vtdlp-whunter-workload`, default credentials) — this is the account the page's own audit describes as "production."
- A second profile (`eb-cli`, account **226388486048**, same IAM username) is also configured locally but was **not** treated as "the logged in account" — the default/active credentials point at 196766403141, and the resource names in that account (e.g. `amplify-vtdlpdev-*`, `dlp-pprd-services-*`) confirm it is the dev/pre-prod account, not the one this page audits.
- Verification method: `aws lambda get-function`, `aws cloudformation list-stacks` / `list-stack-resources`, `aws elasticbeanstalk describe-environments`, `aws s3 ls`. Direct `apigateway:GET` and `lambda:ListFunctions` were denied for this IAM user, so API Gateway and account-wide Lambda enumeration were confirmed indirectly via the CloudFormation stacks that own those resources.

---

## List 1 — Every AWS resource named on the GitBook page

Everything the page names or lists, regardless of whether it turned out to exist. Grouped by service. Wildcard/prefix families from the page's "Out of scope" bullet are kept as the page wrote them (`prefix-*`).

**Lambda functions**
- `amplify-dlpaccess-product-OpenSearchStreamingLambd-GsLGpCgJvWIv`
- `iawav2658176f3PostConfirmation-production`
- `vtdlp_resser_urlredirection`
- `amplify-dlpaccess-product-UpdateRolesWithIDPFuncti-msbSTZWl3JlR`
- `DLP-Access-Lambdas-collectionTitleEditFunction-1FK1XLBZ0FHYH`
- `DLP-Access-Lambdas-createCollectionMapFunction-1LWAGM822QJAL`
- `DLP-Access-Lambdas-createCollectionHeirarchyFuncti-Z4PFL9I6QHOI`
- `DLP-Access-Lambdas-createUpdateFunction-ZUG5P1ML4017`
- `DLP-Access-Lambdas-archiveCollectionHeirarchyFunct-1U4IMUCG518OK`
- `S3toDDB-production-swva-s3toddb-82AXNoulRmcB`
- `VTDLP-IAWA-Ingest-S3toDDB-s3toddb-PM47TUFIZY0B`
- `S3-to-DDB-PROD-s3toddb-1QRSDB8F1O20`
- `S3toDDB-dlp-swva-s3toddb-BKPB8DmYbWnc`
- `vtdlp-resser-urlcreation`
- `amplify-dlpaccess-prod-14-OpenSearchStreamingLambd-oCwQNxIBJ3KQ` (env `prod`, m6rxpkb7…)
- `amplify-dlpaccess-vtdlppr-OpenSearchStreamingLambd-FJTIJrVylGIp` (env `vtdlpprod`, 36nljx…)
- `amplify-vtdlpdlpaccess-al-OpenSearchStreamingLambd-wjZndqLr6KEL` (env `allytest`, qknw6bj…)
- `vtdlp-thumbnail-service`
- `IAWATileGenerationKickOff`
- `vtdlp_iawa_noid_dyno_streamer`
- `csvToDynoTable`
- `changeAttrName`
- `downcaseCategoriesSiteIDs`
- `multiDesc`
- `multiValues`
- `lee_prod_scratch`
- Name-pattern families (page lists these as prefixes, not exact function names): `FixityEvent-*`, `SO0081-PreservationFixityService-*`, `LimitMonitor-*`, `NewNoid-*`, `dlp-services-*` (Mint/Resolution), `VTDLP-Resolution-Service-*`, `update-resolution-new-*`, `tiling-general-*`, `DDBtoDDB-*`, `Iawa-Archive-DDB-copy-*`, `vtdlp-iawa-DDBStreamProcessing-*`, `amplify-login-*`
- Explicitly said **not** to exist by the page's own audit: any Lambda matching `robot`, `sitemap`, `feedback`, `ses`, `mail`, `contact`

**API Gateway REST APIs**
- `vtdlp_resser`
- `NewNoid`
- `SO0081-PreservationFixityService-api`
- `Name Resolution Api Gateway`
- `dlp_minter` (page says two APIs by this description)
- `feedbackapi` — page states this does not exist in production

**CloudFormation stacks**
- `amplify-dlpaccess-production-f9fe0` (root) and its nested stacks: `apicollectionarchives-…-SearchableStack-ZDRD37C4CZ5D`, `functioniawav2658176f3PostConfirmation-1ICJHIWFU7WUZ`, `storageCollectionmap-…`
- `DLP-Access-Lambdas`
- `S3toDDB-production-swva`
- `VTDLP-IAWA-Ingest-S3toDDB`
- `S3-to-DDB-PROD`
- `S3toDDB-dlp-swva`
- `FixityEvent`
- `SO0081-PreservationFixityService` (`PreservationFixityService-ApiGatewayStack-*`, `-StateMachinesStack-*`)
- `LimitMonitor`
- `NewNoid`
- `dlp-services` (`-MintServiceApp-*`, `-ResolutionServiceApp-*`)
- `VTDLP-Resolution-Service`
- `update-resolution-new`
- `tiling-general`
- `DDBtoDDB`
- `Iawa-Archive-DDB-copy`
- `vtdlp-iawa-DDBStreamProcessing`

**S3 buckets**
- `production-dlp-ingest-swva` (used in an illustrative diagram)
- "CollectionMap-yourenv S3 Bucket" (generic placeholder name in body text, not a literal bucket name)

**Elastic Beanstalk**
- `vtdlpprod` environment (described as orphaned / not attached to any Amplify branch)

**Cognito / AppSync**
- Production Cognito User Pool (PostConfirmation trigger)
- 4 AppSync APIs queried by the audit; one ID given per env: `ocrvf7v6rbdyrkx42edgadqo6u` (prod), `m6rxpkb73zehlhwrmyirtfbw3e` (iawa-prod, same API), `36nljxoigjfqbdfsazw5mpztnu` (vtdlpprod, orphaned)

---

## List 2 — Confirmed to exist in the logged-in account (196766403141)

**Lambda functions** (confirmed via `lambda get-function`)
- `amplify-dlpaccess-product-OpenSearchStreamingLambd-GsLGpCgJvWIv`
- `iawav2658176f3PostConfirmation-production`
- `vtdlp_resser_urlredirection`
- `amplify-dlpaccess-product-UpdateRolesWithIDPFuncti-msbSTZWl3JlR`
- `DLP-Access-Lambdas-collectionTitleEditFunction-1FK1XLBZ0FHYH`
- `DLP-Access-Lambdas-createCollectionMapFunction-1LWAGM822QJAL`
- `DLP-Access-Lambdas-createCollectionHeirarchyFuncti-Z4PFL9I6QHOI`
- `DLP-Access-Lambdas-createUpdateFunction-ZUG5P1ML4017`
- `DLP-Access-Lambdas-archiveCollectionHeirarchyFunct-1U4IMUCG518OK`
- `S3toDDB-production-swva-s3toddb-82AXNoulRmcB`
- `VTDLP-IAWA-Ingest-S3toDDB-s3toddb-PM47TUFIZY0B`
- `S3-to-DDB-PROD-s3toddb-1QRSDB8F1O20`
- `S3toDDB-dlp-swva-s3toddb-BKPB8DmYbWnc`
- `vtdlp-resser-urlcreation`
- `vtdlp-thumbnail-service`
- `IAWATileGenerationKickOff`
- `vtdlp_iawa_noid_dyno_streamer`
- `csvToDynoTable`

**CloudFormation stacks** (present in `list-stacks`, status ≠ `DELETE_COMPLETE`)
- `amplify-dlpaccess-production-f9fe0` + all 5 nested stacks listed above
- `DLP-Access-Lambdas`
- `S3toDDB-production-swva`
- `VTDLP-IAWA-Ingest-S3toDDB`
- `S3-to-DDB-PROD`
- `S3toDDB-dlp-swva`
- `FixityEvent`
- `PreservationFixityService` + `PreservationFixityService-ApiGatewayStack-XBN0LT1IW8T8` + `PreservationFixityService-StateMachinesStack-QVPL6TIEFA85`
- `LimitMonitor`
- `NewNoid`
- `dlp-services` + `dlp-services-MintServiceApp-VH77X6D3FAL7` + `dlp-services-ResolutionServiceApp-LJ0H83PLW50B`
- `VTDLP-Resolution-Service`
- `update-resolution-new`
- `tiling-general`
- `DDBtoDDB`
- `Iawa-Archive-DDB-copy`
- `vtdlp-iawa-DDBStreamProcessing` + `vtdlp-iawa-DDBStreamProcessing-Archive`

**API Gateway REST APIs** (confirmed indirectly — the CFN stack owns an `AWS::ApiGateway::RestApi` resource; direct `apigateway:GET` was denied)
- `NewNoid` → REST API id `2xmdyl893j` (logical id `MintApi`) — matches one of the "two `dlp_minter` APIs"
- `SO0081-PreservationFixityService-api` → REST API id `u2tbrq5j8e`
- `dlp-services` Mint API → REST API id `j1lxgg2aak` (logical id `MintApi`) — the second `dlp_minter`-style API
- Resolution API → REST API id `zjxfzd5xih` (`dlp-services-ResolutionServiceApp`) and a second one, id `ltghm34375` (`VTDLP-Resolution-Service`) — one of these is the "Name Resolution Api Gateway" the page refers to; could not disambiguate which without `apigateway:GET`
- `vtdlp_resser` — the page itself notes this API's Lambda (`vtdlp_resser_urlredirection`/`vtdlp-resser-urlcreation`) is **hand-created, not in any CFN stack**; the Lambda side is confirmed to exist (see above), but the REST API resource itself could not be independently confirmed due to the `apigateway:GET` permission denial

**Elastic Beanstalk**
- `vtdlpprod` environment — confirmed (`CNAME: dlp-ingest.us-east-1.elasticbeanstalk.com`, Status: Ready)

**S3 buckets** (present in this account, though named differently than the page's illustrative example — see List 3)
- `amplify-dlpaccess-production-f9fe0-deployment`
- `collectionmapf9fe0-production` — this is almost certainly the real bucket behind the page's generic "CollectionMap-yourenv S3 Bucket" description
- `tiling-general-batch-deposit-196766403141`
- `vtdlp-s3-tunnel-prod`
- (full bucket list retrieved; only buckets plausibly tied to page content are listed here)

---

## List 3 — Named on the page but NOT found in the logged-in account

- `amplify-dlpaccess-prod-14-OpenSearchStreamingLambd-oCwQNxIBJ3KQ` — no such Lambda in this account
- `amplify-dlpaccess-vtdlppr-OpenSearchStreamingLambd-FJTIJrVylGIp` — no such Lambda in this account
- `amplify-vtdlpdlpaccess-al-OpenSearchStreamingLambd-wjZndqLr6KEL` — no such Lambda in this account
- `changeAttrName` — no such Lambda in this account (a function with the same name exists in the other, dev/pre-prod account, 226388486048)
- `downcaseCategoriesSiteIDs` — not found (a similarly-named `downcaseSiteIDs` exists only in the dev/pre-prod account)
- `multiDesc` — not found
- `multiValues` — not found
- `lee_prod_scratch` — not found
- `amplify-login-*` family — no matching CloudFormation stack and no way to enumerate by prefix without `lambda:ListFunctions`; no evidence found in this account
- `production-dlp-ingest-swva` (S3 bucket) — no bucket by this name in this account; appears to be an illustrative/generic name in the diagram rather than a real bucket
- `feedbackapi` (REST/HTTP API) — confirmed absent; consistent with the page's own conclusion that this API does not exist in production
- Any Lambda matching `robot`, `sitemap`, `feedback`, `ses`, `mail`, `contact` — confirmed absent, consistent with the page's own audit

### Notes / caveats
- The IAM user used for this check (`vtdlp-whunter-workload` in account 196766403141) lacks `lambda:ListFunctions` and `apigateway:GET`, so nothing here is a full enumeration — absence above means "not found by the specific name given," not "proven impossible to exist under some other name."
- Several long, auto-generated resource suffixes (CDK/Amplify hash suffixes) were read from screenshots of the GitBook page and are subject to OCR transcription risk (e.g. `l` vs `1`, `O` vs `0`); where a CloudFormation `list-stack-resources` call could resolve the exact physical ID, that authoritative value was used instead of the screenshot text.
