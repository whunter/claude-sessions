# Hand-off: gitbook-aws-inventory-review

**Deliverable:** `gitbook-aws-inventory-review.md` (this directory) — the three-list AWS resource cross-check the user asked for.
**Source doc:** GitBook page "Lambda inventory prod" (VTUL-DLP space, change request #20 "Restore original Lambda flow layout")
https://app.gitbook.com/o/TvFOuK5Ys0OrTXXA3B6X/s/1wMf6kajAYFiqHU5KNPP/~/edit/~/changes/20/elastic-beanstalk-and-cdk-implementation-timeline/lambda-inventory-prod

## What's done

The task is complete. `gitbook-aws-inventory-review.md` contains three lists, each organized by AWS service (Lambda, API Gateway, CloudFormation, S3, Elastic Beanstalk, Cognito/AppSync):

1. **List 1** — every AWS resource named anywhere on the GitBook page (diagrams, tables, and body text), regardless of whether it turned out to exist.
2. **List 2** — the subset of List 1 confirmed to exist in the logged-in AWS account (196766403141, `vtdlp-whunter-workload`).
3. **List 3** — the subset of List 1 confirmed **not** to exist in that account.

## How the check was done

- The GitBook page renders its content as image-styled code blocks and rich-text blocks, so `get_page_text`/the accessibility tree only returned truncated (~100-char) fragments. I read the full page by scrolling through the Editor view and taking `zoom` screenshots of each table/diagram section — this is why a couple of long CDK/Amplify hash suffixes carry OCR risk (`l` vs `1`, `O` vs `0`).
- AWS verification used the `aws` CLI already configured in this environment, against the **default** credentials (account 196766403141 — confirmed to be "production" both because the page calls it that and because a second local profile, `eb-cli` → account 226388486048, contains obviously dev/pre-prod-named resources like `amplify-vtdlpdev-*`).
- The IAM user has **no** `lambda:ListFunctions` and **no** `apigateway:GET` — so nothing here is a full account enumeration. Verification was name-by-name (`lambda get-function <name>`) and stack-by-stack (`cloudformation list-stack-resources <stack>` to pull authoritative physical resource IDs, which is also how the OCR-risk suffixes were double-checked/corrected). API Gateway REST APIs were confirmed indirectly, via the CloudFormation stack that owns each `AWS::ApiGateway::RestApi` resource.

## What's NOT done / caveats to flag if this comes up again

1. **Not a full enumeration.** "Not found" in List 3 means "not found under the specific name the page gave," not "proven to not exist under any name." If `lambda:ListFunctions`/`apigateway:GET` get granted to this user later, it'd be worth re-running a full `list-functions`/`get-rest-apis` diff against List 1 for a stronger negative-confirmation.
2. **Ambiguous "Name Resolution Api Gateway".** Two candidate REST APIs matched this description (`dlp-services-ResolutionServiceApp` → id `zjxfzd5xih`, and `VTDLP-Resolution-Service` → id `ltghm34375`). Both are listed in List 2 as candidates; I could not disambiguate which one the page's audit meant without `apigateway:GET` access to check custom domain / stage names.
3. **`vtdlp_resser` REST API.** The page itself says this API's Lambda is hand-created and not in any CloudFormation stack, so I could confirm the Lambda side exists but not the API Gateway resource itself (no CFN owner to check, and direct `apigateway:GET` is denied).
4. **Three "other-environment duplicate" OpenSearch Lambdas** (prod/vtdlpprod/allytest variants from the page's "Other-environment duplicates" table) came back not-found by the exact screenshot-read name. Given the OCR risk noted above, if this matters, it's worth re-reading that specific table region at higher zoom, or re-checking against the account behind the `vtdlpprod`/`allytest` Amplify branches directly if credentials for those are ever available.

## Key files

- `gitbook-aws-inventory-review.md` — the actual deliverable (three lists + methodology + caveats section at the bottom).
