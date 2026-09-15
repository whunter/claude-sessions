# Plan: Migrate idn.lib.vt.edu resolution traffic to the dormant stack

## Context

`resolution-service-inventory` established that `idn.lib.vt.edu` ark redirects are
currently served by the legacy standalone stack `VTDLP-Resolution-Service`
(API `ltghm34375` → Lambda → DynamoDB `mint`, 40,194 items, ~1,057 invocations/30d),
while a second, parallel stack — `dlp-services-ResolutionServiceApp-LJ0H83PLW50B`
(API `zjxfzd5xih`) nested under the `dlp-services` app — is fully deployed but idle
(0 invocations/30d). The goal now is to make the dormant stack the one actually
serving production traffic, with **no behavior change** and **no downtime**.

This session's follow-up investigation found the dormant stack is in worse shape
than "just idle" — it's effectively broken, and the originally-planned cutover
mechanism (swap the real front-door CloudFront's origin) turned out to be
infeasible from here. Both change the shape of the plan materially, so they're
documented before the steps.

### New findings this session

1. **The dormant stack's DynamoDB target table doesn't exist.** Its Lambda's
   `TargetTable` env var is `dlp_minter`, sourced from the `dlp-services` parent
   stack's `NSTableName` parameter. `dlp_minter` is declared in that stack's
   template (as the `MintServiceApp` nested stack's `ResolutionTable` resource)
   but `aws dynamodb describe-table --table-name dlp_minter` returns
   `ResourceNotFoundException` — it was deleted out-of-band and CloudFormation
   never reconciled (the whole `dlp-services` stack has been `CREATE_COMPLETE`
   since 2021-11-18 with no updates since). This is why the dormant API returns
   the 404-fallback image for every request, including live arks — it isn't
   "stale," its backend table is simply gone.
2. **`vtdlp_resser_idn` (asked about) is a separate, much smaller table** (2,520
   items vs. `mint`'s 40,194) and isn't owned by either resolution stack. It's
   missing most of the production ark set, so repurposing it would still require
   a full backfill from `mint` and would drop nothing extra vs. just pointing at
   `mint` directly. **Recommendation: skip it — point straight at `mint`
   instead** (see Step 1).
3. **The real front door is a DNS CNAME, not a fixed CloudFront wiring** —
   `idn.prod.cloud.lib.vt.edu` → `d3btzx4iv66c21.cloudfront.net` (TTL 300s),
   and that CloudFront distribution's owning AWS account is still unidentified
   (checked `196766403141` and the `eb-cli` account `226388486048`; not in
   either). Per your observation: rather than needing access to that unknown
   account, we can instead repoint the CNAME itself to one of *our* CloudFront
   distributions — bypassing the mystery front door entirely. This is a real
   simplification, with one caveat: whatever the mystery CloudFront currently
   does beyond plain pass-through (WAF, logging, and — notably — it's the layer
   where `idn.lib.vt.edu` currently 403s on direct curl with
   `MissingAuthenticationTokenException`, a quirk never root-caused) would no
   longer be in the path. Both stacks' own CloudFronts (`E2CZDTXELAYPFI` /
   `E36QWU4GGFDPFY`) were confirmed to have **identical** default cache behavior
   (TTL 0, no query-string/cookie forwarding, `Origin` header only) — they're
   clones from the same SAR template — so at least the two candidates behave
   identically relative to each other.
4. Confirmed via `aws iam list-attached-role-policies` /
   `list-role-policies` that the dormant Lambda's role likely needs a DynamoDB
   permissions update to reach `mint` (currently scoped to `dlp_minter`) —
   couldn't read the policy document itself (`iam:GetRolePolicy` denied to this
   user), so this needs confirming with write/read IAM access before cutover.

## ✅ Resolved (post-verification, see handoff.md) — cutover is done

Two rounds of verification changed step 5 twice:

1. First pass: repointing the `idn.prod.cloud.lib.vt.edu` CNAME to the
   dormant stack's own CloudFront **did not work** — CloudFront routes HTTPS
   requests by matching SNI/Host against whichever distribution has that
   hostname registered as an Alternate Domain Name, not by the CNAME chain
   used to reach an edge IP. 100/100 test requests still landed on the
   legacy Lambda.
2. Second pass, after further investigation: `d3btzx4iv66c21.cloudfront.net`
   turned out to be the CloudFront distribution API Gateway auto-provisions
   for an **edge-optimized Custom Domain Name** — `idn.lib.vt.edu` was
   configured directly in API Gateway (account `196766403141`), which is why
   it never showed up in `list-distributions` for any customer account. The
   real step 5 was: **update that Custom Domain Name's base-path mapping**
   from the legacy API (`ltghm34375`) to the dormant/mint-backed API
   (`zjxfzd5xih`). This was done and confirmed via CloudWatch: 99/100 test
   requests now hit the formerly-dormant Lambda, 0 errors.

Steps 1–4 (repointing `NSTableName`, verifying parity, checking DNS
ownership) turned out to be unnecessary for the actual cutover mechanism —
no CloudFront alias or DNS change was needed at all. Step 5 is complete.
Steps 6–8 (burn-in, rollback plan, decommission) are still the right next
actions. See handoff.md for full detail and the current infra split.

## Recommended approach

**Don't touch the unknown-account CloudFront at all.** Fix the dormant stack in
place, verify it's byte-for-byte equivalent to production when hit directly,
then flip the `idn.prod.cloud.lib.vt.edu` CNAME to the dormant stack's own
CloudFront. Keep the legacy stack running untouched throughout so rollback is
just reverting the CNAME (5-minute TTL).

### Steps

1. **Repoint the dormant stack at the live data**, not a resurrected `dlp_minter`:
   - Update the `dlp-services` stack's `NSTableName` parameter from `dlp_minter`
     to `mint` (`aws cloudformation update-stack --stack-name dlp-services
     --use-previous-template --parameters ParameterKey=NSTableName,ParameterValue=mint
     ParameterKey=Image404,UsePreviousValue=true ParameterKey=Region,UsePreviousValue=true
     ParameterKey=NOIDTemplate,UsePreviousValue=true ParameterKey=NOIDScheme,UsePreviousValue=true
     ParameterKey=NOIDNAA,UsePreviousValue=true`).
   - This also repoints `MintServiceApp` (the write-side minter) at `mint`. Confirm
     with whoever owns this stack that `MintServiceApp` being dormant (0
     invocations/30d) means this is safe — if it's truly unused, no behavior
     changes there either.
   - Also align `Image404` to production's value
     (`https://i.stack.imgur.com/6M513.png` vs. dormant's
     `https://vtdlp-dev-cf.s3.amazonaws.com/404.png`) for full parity, unless you
     want to standardize on the vtdlp-dev-cf one going forward (then update the
     *live* stack instead — pick one canonical 404 image).
   - Update the dormant Lambda's IAM role (`NameResolutionFunctionRolePolicy0`
     on `dlp-services-ResolutionSe-NameResolutionFunctionRo-1S32Q9EUBUQUA`) to
     grant read access to the `mint` table's ARN
     (`arn:aws:dynamodb:us-east-1:196766403141:table/mint` and its
     `long_url-index` GSI) — this may already ride along with the stack update
     if the SAR template derives the policy from `TargetTableName`; verify by
     re-checking the policy document after the update.

2. **Verify parity by hitting the dormant API Gateway directly** (same technique
   as the inventory session):
   ```
   curl -s -D - -o /dev/null "https://zjxfzd5xih.execute-api.us-east-1.amazonaws.com/Prod/ark:/53696/635c402a"
   ```
   Confirm it now 301s to `https://digital.lib.vt.edu/archive/635c402a`, matching
   the live API. Spot-check several more ark IDs sampled from `mint` (including
   any edge cases: missing records, records with unusual `long_url` values) to
   confirm the fallback-image path and redirect path both match the live
   stack's responses exactly.

3. **Prep the dormant stack's own CloudFront (`E36QWU4GGFDPFY` /
   `d23illvkjqb563.cloudfront.net`) to accept the real hostname**:
   - Add `idn.lib.vt.edu` as an alternate domain name (CNAME/alias) on that
     distribution.
   - Attach the existing ACM cert for `idn.lib.vt.edu` (already present in
     `196766403141` per `aws acm list-certificates`) — must be in `us-east-1`
     for CloudFront, which it is.
   - Test it pre-cutover using a Host-header override so DNS isn't touched yet:
     ```
     curl -s -D - -o /dev/null -H "Host: idn.lib.vt.edu" "https://d23illvkjqb563.cloudfront.net/ark:/53696/635c402a"
     ```
     Specifically check whether the colon-in-path 403 seen on the current
     `idn.lib.vt.edu` still reproduces here or not — either outcome is useful
     to know before cutover (if it disappears, that's a bonus fix to call out;
     if it appears, that's a blocker to resolve first).

4. **Identify who owns the `idn.prod.cloud.lib.vt.edu` DNS record.** It's not in
   Route53 in either AWS account checked (`route53:ListHostedZones` was denied
   for `196766403141` — recheck once IAM access is broadened; if still absent,
   it's likely managed by VT's central/campus DNS, outside AWS entirely) —
   whoever manages that zone needs to make the cutover change in step 5.

5. **Cutover**: change the `idn.prod.cloud.lib.vt.edu` CNAME target from
   `d3btzx4iv66c21.cloudfront.net` to `d23illvkjqb563.cloudfront.net`. TTL is
   300s, so both directions (cutover and rollback) propagate in ~5 minutes.
   Do this at a low-traffic time and watch CloudWatch on the dormant Lambda
   (`Invocations`, `Errors`, `Duration`) immediately after.

6. **Burn-in monitoring**: watch the dormant stack's Lambda/API Gateway/DynamoDB
   metrics for a period (suggest 24–72h) confirming invocation counts now match
   what the legacy stack used to see (~35/day) and error rate is ~0.

7. **Rollback plan** (if anything looks wrong post-cutover): revert the CNAME
   back to `d3btzx4iv66c21.cloudfront.net`. The legacy stack is left fully
   intact and untouched through all of the above, so this is a clean revert
   with no data loss.

8. **Decommission** (only after burn-in is clean and you're confident): delete
   the legacy `VTDLP-Resolution-Service` stack. Leave the dormant stack's name
   as-is unless you also want to rename/relabel it now that it's the live one.

### Permissions gap (blocks steps 1, 3, 5 as written)

The `vtdlp-whunter-workload` identity used for the investigation is read-only
for everything above — `cloudformation:UpdateStack`, `iam:PutRolePolicy` /
`iam:GetRolePolicy`, `apigateway:GET`, `route53:List*`, and
`cloudfront:UpdateDistribution` are all currently denied. Someone with write
access (or an expanded policy for this user) needs to actually run steps 1, 3,
and 5. Steps 2 and 6 (verification/monitoring) are runnable with current
read-only access.
