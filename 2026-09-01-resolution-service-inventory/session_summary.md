# Session: Trace which AWS resources serve idn.lib.vt.edu ark redirects

**Date:** 2026-09-01
**Account(s):** `196766403141` (primary, default profile), `226388486048` (`--profile eb-cli`)
**Goal:** Given `http://idn.lib.vt.edu/ark:/53696/635c402a` — an API-Gateway-fronted URL that calls a Lambda, which reads DynamoDB, to redirect the user to another page — determine exactly which service instances are *actually* in use, since the account is expected to have multiple candidate deployments.

## Investigation, in order

1. **Confirmed AWS identity/access**: `aws sts get-caller-identity` → account `196766403141`, user `vtdlp-whunter-workload`. This user has broad `List`/`Describe` and CloudWatch read access but is denied `apigateway:GET`, `lambda:ListFunctions`, `iam:List*`, and `tag:GetResources` — so API Gateway/Lambda inventories had to be reconstructed via CloudFormation rather than direct service listing.

2. **Resolved the DNS/CDN chain** for `idn.lib.vt.edu`:
   ```
   idn.lib.vt.edu --CNAME--> idn.prod.cloud.lib.vt.edu --CNAME--> d3btzx4iv66c21.cloudfront.net
   ```
   A direct `curl` to the URL returned `301` (CloudFront) then `403 MissingAuthenticationTokenException` (API Gateway's "no matching resource" error) on the HTTPS hop — meaning the front-end CloudFront reaches an API Gateway, but the specific probe path didn't route cleanly through it. Flagged as an open thread rather than chased further, since that CloudFront distro isn't in a reachable account.

3. **Searched for the CloudFront distro's owning account.** `aws cloudfront list-distributions` in `196766403141` listed 6 distributions, none matching `d3btzx4iv66c21.cloudfront.net`. The user then pointed out an `eb-cli` AWS CLI profile exists; `aws sts get-caller-identity --profile eb-cli` showed it belongs to a *second* account, `226388486048`. Checked that account's 5 CloudFront distributions too — still no match. The real front-door distribution's account remains unidentified.

4. **Found candidate backend resources via DynamoDB and CloudFormation**, since direct API Gateway/Lambda listing was denied:
   - `aws dynamodb list-tables` surfaced `vtdlp_resser_idn` and `mint` as name-resolution-shaped tables (both keyed on `short_id`), but `dynamodb:GetItem` was denied, so contents couldn't be read directly.
   - `aws cloudformation list-stacks` surfaced two parallel "resolution service" stacks: the older standalone `VTDLP-Resolution-Service`, and a newer one nested under `dlp-services` (`dlp-services-ResolutionServiceApp-LJ0H83PLW50B`) alongside a sibling `MintServiceApp` stack. Two more standalone stacks (`updateResolution`, `update-resolution-new`) also exist but turned out to be write-side (`updateResolutionFunction`), not the read/redirect path.
   - `aws cloudformation list-stack-resources` on each resolution stack mapped logical IDs to physical AWS resources: each stack has its own API Gateway REST API (`ltghm34375` old, `zjxfzd5xih` new), its own Lambda (`NameResolutionFunction`), and its own CloudFront distribution (`E2CZDTXELAYPFI` old, `E36QWU4GGFDPFY` new) — none of which turned out to be the real internet-facing CloudFront either.

5. **Determined which stack is actually live** using CloudWatch metrics — the decisive step, since both stacks are fully deployed and neither's CloudFront distro is the real front door, so "which one exists" wasn't enough:
   - `aws cloudwatch get-metric-statistics` for `AWS/Lambda Invocations` over the trailing 30 days: the old stack's Lambda had **1,057** invocations; the new stack's Lambda had **0**.
   - `aws lambda get-function-configuration` on the live Lambda showed env var `TargetTable=mint` — correcting an earlier assumption that `vtdlp_resser_idn` (the more suggestively-named table) was the one in use. `mint` has 40,194 items and ~721 consumed read-capacity-units over 30 days, consistent with active traffic; `vtdlp_resser_idn` only had ~6.5 RCU/30d, consistent with it being a much smaller/different or legacy dataset.
   - `aws cloudwatch list-metrics --namespace AWS/ApiGateway` was needed to discover the correct dimension names (`ApiName`/`Stage` — both APIs share the ApiName "Name Resolution Api Gateway" from the shared template, so this metric alone couldn't distinguish the two APIs).

6. **Final confirmation by direct request**, bypassing the unreachable front-door CloudFront and hitting each API Gateway's default `execute-api` endpoint with the identical ark path:
   - `ltghm34375` (old/live stack) → `301 Location: https://digital.lib.vt.edu/archive/635c402a` — a genuine resolved record.
   - `zjxfzd5xih` (new/dormant stack) → `301 Location: https://vtdlp-dev-cf.s3.amazonaws.com/404.png` — the Lambda's not-found fallback image, meaning its backing data doesn't have this record (consistent with 0 invocations meaning it isn't in the live traffic path, though the API itself is reachable and returns a coherent "not found" response rather than an error).

## Conclusion

The `idn.lib.vt.edu` ark-resolution request is served, within account `196766403141`, by:
- **API Gateway:** `ltghm34375` ("Name Resolution Api Gateway", stage `Prod`)
- **Lambda:** `VTDLP-Resolution-Service-NameResolutionFunction-1IZLCRWFTW5NY`
- **DynamoDB table:** `mint`

The parallel `dlp-services-ResolutionServiceApp-LJ0H83PLW50B` stack (API `zjxfzd5xih`, its own `NameResolutionFunction` Lambda, CloudFront `E36QWU4GGFDPFY`/`d23illvkjqb563.cloudfront.net`) is fully deployed but not receiving production traffic.

## Open threads (see handoff.md for detail)

- The real internet-facing CloudFront distribution (`d3btzx4iv66c21.cloudfront.net`) is in neither `196766403141` nor `226388486048` — owning account still unknown.
- Direct `curl` to `idn.lib.vt.edu` 403s at the CloudFront→API Gateway hop even though the backend itself works fine when hit directly — likely a `:` encoding/caching quirk in that unreachable CloudFront config.
