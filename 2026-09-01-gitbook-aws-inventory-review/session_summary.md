# Session Summary: gitbook-aws-inventory-review

## Request

The user asked me to review a specific GitBook page — "Lambda inventory prod" in the VTUL-DLP space, an in-progress AI-agent-edited change request (#20, "Restore original Lambda flow layout") — and extract the names/ARNs of every AWS service the page references. They asked for three lists, all organized by AWS service, written to one markdown file:

1. Every instance found on the page.
2. Only the instances from that list that actually exist in the logged-in AWS account.
3. Only the instances from that list that do **not** exist in the logged-in AWS account.

## What I did

1. **Loaded the `claude-in-chrome` skill and browser tools**, then navigated to the GitBook URL the user provided.
2. **Discovered that standard text extraction didn't work.** GitBook renders this page's diagrams and tables inside styled blocks that `get_page_text` returns as near-empty, and the accessibility tree (`read_page`) truncates every text node to ~100 characters regardless of the `max_chars` budget requested. Preview mode was also unavailable (the space isn't published as a docs site).
3. **Fell back to visual reading**: closed the AI-agent side panel and page sidebar for room, then scrolled through the entire page in the Editor view, taking `zoom` screenshots of each diagram/table section to read the full, untruncated text. This surfaced the page's real content: several generic explanatory diagrams (illustrating "how a Lambda gets invoked") followed by the actual inventory — tables of real Lambda function names, their CloudFormation stacks, an environment/branch map, a "disposition matrix" (bucket A/B/C/D classification for migration planning), a dormant "DLP-Access-Lambdas" stack, an "ingest pipelines" table, an "other-environment duplicates" table, and an "out of scope — unrelated services" list of Lambda name patterns.
4. **Cross-checked every named resource against the live AWS account** using the `aws` CLI already available in this environment:
   - Confirmed the default credentials (account `196766403141`, user `vtdlp-whunter-workload`) are the right account to check against — it's the one the page itself describes as production. A second local profile (`eb-cli`, account `226388486048`) turned out to be a separate dev/pre-prod account (confirmed by its own resource names, e.g. `amplify-vtdlpdev-*`), so I did not treat it as "the logged in account."
   - `lambda:ListFunctions` and `apigateway:GET` were both denied for this IAM user, so I couldn't do a blanket enumeration. Instead I checked resources one at a time: `aws lambda get-function --function-name <name>` for individual Lambdas, and `aws cloudformation list-stacks` / `list-stack-resources` to confirm stacks and pull the *authoritative* physical resource IDs for Lambdas and API Gateway REST APIs owned by those stacks (this also let me correct a couple of screenshot-OCR mistakes in long hash suffixes, e.g. `S3-to-DDB-PROD-s3toddb-1QRSDB8F1O2O` read from the screenshot vs. the real `…1QRSDB8F1O20`).
   - Confirmed the `vtdlpprod` Elastic Beanstalk environment exists and is `Ready`.
   - Checked S3 buckets via `aws s3 ls` and matched the page's generic "CollectionMap-yourenv S3 Bucket" placeholder to the real bucket `collectionmapf9fe0-production`.
5. **Wrote the three-list deliverable** to `gitbook-aws-inventory-review.md` in this directory, organized by service (Lambda, API Gateway, CloudFormation, S3, Elastic Beanstalk, Cognito/AppSync) with a short methodology note and a caveats section covering the permission limits and OCR risk.

## Key outcome

- Most of the page's core production inventory checks out: the `DLP-Access-Lambdas` stack (5 dormant Lambdas), the four S3→DynamoDB ingest Lambdas, the production OpenSearch-streaming and Cognito PostConfirmation Lambdas, and the NewNoid/Fixity/Resolution service stacks all exist as named.
- Several items do **not** exist under the exact name given: the three "other-environment duplicate" OpenSearch Lambdas (prod/vtdlpprod/allytest variants), a handful of one-off maintenance scripts (`changeAttrName`, `multiDesc`, `multiValues`, `lee_prod_scratch`, `downcaseCategoriesSiteIDs`), and — as the page's own audit already concluded — `feedbackapi` and any robots/sitemap/feedback-SES Lambda.
- Two "dlp_minter"-style Mint APIs and a "Name Resolution Api Gateway" were confirmed to exist via their owning CloudFormation stacks, though I could not fully disambiguate which of two resolution-service REST APIs the page meant, since direct API Gateway read access is denied for this IAM user.

## Not done / open threads

- No full account-wide enumeration was possible (missing `lambda:ListFunctions`/`apigateway:GET`) — see the caveats section in `gitbook-aws-inventory-review.md` and `handoff.md` for what a stronger follow-up check would need.
- The `vtdlp_resser` REST API itself (as opposed to its Lambda) couldn't be independently confirmed — the page notes it's hand-created outside CloudFormation, so there was no stack to check it against.
