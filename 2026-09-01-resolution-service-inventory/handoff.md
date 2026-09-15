# Hand-off: resolution-service-inventory

**Goal:** For `http://idn.lib.vt.edu/ark:/53696/635c402a`, identify which actual AWS service instances (API Gateway, Lambda, DynamoDB table) handle the request in account `196766403141`, given that two parallel "resolution service" deployments exist.

## What's done

Full request path traced and confirmed live vs. dormant resources:

**DNS chain:**
```
idn.lib.vt.edu  --CNAME-->  idn.prod.cloud.lib.vt.edu  --CNAME-->  d3btzx4iv66c21.cloudfront.net
```
- `dig +short idn.lib.vt.edu` and `dig idn.lib.vt.edu ANY` used to confirm this.
- `d3btzx4iv66c21.cloudfront.net` was checked against `aws cloudfront list-distributions` in **both** `196766403141` (default profile) and `226388486048` (`--profile eb-cli`) — not present in either. It belongs to a third, still-unidentified AWS account. Not resolved this session.

**Two parallel resolution-service CloudFormation stacks exist in `196766403141`:**

| | Live | Dormant |
|---|---|---|
| Stack | `VTDLP-Resolution-Service` | `dlp-services-ResolutionServiceApp-LJ0H83PLW50B` (nested under `dlp-services`) |
| API Gateway | `ltghm34375` ("Name Resolution Api Gateway", stage `Prod`) | `zjxfzd5xih` (same name, stage `Prod`) |
| Lambda | `VTDLP-Resolution-Service-NameResolutionFunction-1IZLCRWFTW5NY` | `dlp-services-ResolutionServ-NameResolutionFunction-1ttBuMQ1rMrp` |
| CloudFront (own stack's distro, NOT the real front door) | `E2CZDTXELAYPFI` / `dqj0aemr2jkhf.cloudfront.net` | `E36QWU4GGFDPFY` / `d23illvkjqb563.cloudfront.net` |
| DynamoDB table (`TargetTable` env var on Lambda) | `mint` (40,194 items) | not confirmed — record not found for this ark |
| 30-day Lambda invocations | 1,057 | 0 |

**Confirmation of which is live** — hit both API Gateways' `execute-api` endpoints directly with the same ark path:
```sh
curl -s -D - -o /dev/null "https://ltghm34375.execute-api.us-east-1.amazonaws.com/Prod/ark:/53696/635c402a"
# -> 301, Location: https://digital.lib.vt.edu/archive/635c402a   (real hit in `mint` table)

curl -s -D - -o /dev/null "https://zjxfzd5xih.execute-api.us-east-1.amazonaws.com/Prod/ark:/53696/635c402a"
# -> 301, Location: https://vtdlp-dev-cf.s3.amazonaws.com/404.png (fallback, record not found)
```

**Conclusion:** the request is actually served by `ltghm34375` → `VTDLP-Resolution-Service-NameResolutionFunction-1IZLCRWFTW5NY` → DynamoDB table `mint`. The `dlp-services-ResolutionServiceApp` stack is deployed but dead.

## What's NOT done / open threads

1. **The real front-door CloudFront (`d3btzx4iv66c21.cloudfront.net`) is in neither `196766403141` nor `226388486048`.** Its account is unidentified — would need another profile/role or someone with broader org access to pin down.
2. **`idn.lib.vt.edu` itself returns `403 MissingAuthenticationTokenException`** when curled directly (`http://idn.lib.vt.edu/ark:/53696/635c402a` → redirects to https → 403), even though hitting `ltghm34375` directly works fine. Suspected cause: the external CloudFront distro mishandling the `:` in `ark:/...` (encoding/caching quirk) before it reaches API Gateway — not investigated further since that CloudFront isn't in an account we have access to.
3. No IAM/API Gateway resource browsing is possible for this user directly (`apigateway:GET`, `lambda:ListFunctions`, `tag:GetResources`, `iam:List*` are all denied) — everything above was cross-referenced via CloudFormation (`list-stacks` / `list-stack-resources`, which *are* allowed) plus targeted `lambda:GetFunctionConfiguration`, `dynamodb:DescribeTable`, and CloudWatch metrics. If deeper API Gateway inspection is ever needed, this user's policy would need `apigateway:GET` added.

## Key commands used (reusable for future audits)

```sh
aws sts get-caller-identity                          # confirm account/identity
aws cloudformation list-stacks                        # find candidate stacks
aws cloudformation list-stack-resources --stack-name <name>   # map logical->physical resource IDs
aws lambda get-function-configuration --function-name <name>  # env vars incl. TargetTable
aws dynamodb describe-table --table-name <name>       # schema/item count (GetItem is denied)
aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Invocations ...
aws cloudwatch list-metrics --namespace AWS/ApiGateway   # find correct dimension names (ApiName/Stage)
aws cloudfront list-distributions [--profile eb-cli]   # cross-account distro lookup
```
