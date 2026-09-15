# Session: Plan migration of resolution-service traffic to the dormant stack

**Date:** 2026-09-01
**Account:** `196766403141` (default profile, read-only user `vtdlp-whunter-workload`)
**Goal:** Starting from the prior `resolution-service-inventory` session's findings
(two parallel resolution-service stacks, one live one dormant), plan how to move
production `idn.lib.vt.edu` traffic onto the dormant stack without changing
behavior or causing downtime.

## Investigation, in order

1. **Compared both Lambdas' env vars.** Live (`VTDLP-Resolution-Service-...`):
   `TargetTable=mint`, `Image404=https://i.stack.imgur.com/6M513.png`. Dormant
   (`dlp-services-ResolutionServ-...`): `TargetTable=dlp_minter`,
   `Image404=https://vtdlp-dev-cf.s3.amazonaws.com/404.png`.
2. **Checked whether `dlp_minter` exists** — it doesn't
   (`dynamodb describe-table` → `ResourceNotFoundException`). `aws dynamodb
   list-tables` confirmed only `mint` and `vtdlp_resser_idn` exist as
   name-resolution-shaped tables; `dlp_minter` is absent entirely.
3. **Tried to inspect the front-door → API Gateway link directly**
   (`apigateway:GET`, `route53:ListHostedZones`) — both denied. `acm
   list-certificates` did succeed and showed a cert for `idn.lib.vt.edu`
   already provisioned in this account.
4. **Diffed both stacks' CloudFormation resources** (`list-stack-resources`) —
   neither declares a custom domain name / base path mapping resource, so the
   real `idn.lib.vt.edu` routing isn't defined in either resolution stack.
5. **Checked stack parameters** — confirmed `TargetTableName` (`NSTableName` at
   the parent) and `Image404` are CloudFormation parameters, not hardcoded, so
   fixing the dormant stack's table is a parameter update + redeploy, not a
   code change.
6. **Traced `NSTableName` to `MintServiceApp`** — the same parameter also feeds
   the sibling `MintServiceApp` nested stack, whose `ResolutionTable` resource
   *is* `dlp_minter` (declared in CFN, but the actual DynamoDB table is gone —
   drift, not a naming coincidence). `dlp-services` has been `CREATE_COMPLETE`
   since 2021-11-18 with zero updates since; `MintServiceApp`'s function also
   shows 0 invocations/30d, i.e. the entire nested app is dead, not just the
   resolution half.
7. **Checked `vtdlp_resser_idn`** (asked about as a possible repointing target)
   — real table, 2,520 items, not owned by any resolution CFN stack, and far
   short of `mint`'s 40,194 items. Concluded it's not a useful target without a
   backfill from `mint` anyway, so recommended skipping it in favor of pointing
   directly at `mint`.
8. **Investigated the front-door bypass idea** (raised by the user): since
   `idn.prod.cloud.lib.vt.edu` is just a CNAME to
   `d3btzx4iv66c21.cloudfront.net` (an unidentified-account CloudFront), rather
   than needing access to that account, the CNAME itself can be repointed to
   one of *our* CloudFront distributions instead. Verified both stacks' own
   CloudFront distributions (`E2CZDTXELAYPFI` live, `E36QWU4GGFDPFY` dormant)
   have identical default cache behaviors (TTL 0, no query string/cookie
   forwarding, `Origin` header only forwarded) and that neither currently has
   any alternate domain alias configured. Checked the CNAME's TTL (300s) for
   rollback-speed purposes.

## Conclusion / plan produced

Wrote a full migration plan (`plan.md` in this session directory) recommending:
1. Repoint the dormant stack's `NSTableName` parameter from `dlp_minter` to
   `mint` (skip resurrecting `dlp_minter` or repurposing `vtdlp_resser_idn` —
   both would need a backfill from `mint` with no benefit over using it
   directly), and verify/update the dormant Lambda's IAM role to read the
   `mint` table + `long_url-index` GSI.
2. Verify parity by hitting `zjxfzd5xih`'s `execute-api` endpoint directly with
   sampled ark IDs from `mint`.
3. Add `idn.lib.vt.edu` as an alias on the dormant stack's own CloudFront
   (`E36QWU4GGFDPFY`), attach the existing ACM cert, and pre-test with a
   Host-header override — specifically checking whether the still-unexplained
   colon-in-ark-path 403 (seen on direct curls to `idn.lib.vt.edu` today)
   reproduces on this path.
4. Identify who manages the `idn.prod.cloud.lib.vt.edu` DNS record (not found
   in Route53 for either AWS account checked so far).
5. Cutover: repoint that CNAME to the dormant CloudFront's domain
   (`d23illvkjqb563.cloudfront.net`); 300s TTL means both cutover and rollback
   propagate in ~5 minutes, and the legacy stack is left untouched throughout
   for a clean revert.
6. Burn-in monitoring, then decommission the legacy `VTDLP-Resolution-Service`
   stack once confidence is high.

**Execution blocker:** the read-only `vtdlp-whunter-workload` identity used
this session cannot run any of the actual write steps
(`cloudformation:UpdateStack`, `iam:PutRolePolicy`/`GetRolePolicy`,
`apigateway:GET`, `route53:List*`, `cloudfront:UpdateDistribution` all denied).
The plan is written as a runbook for whoever has write access, not something
executed in this session.

## First verification pass (after user repointed the dormant Lambda + CNAME)

User applied the backend fix directly (not via CloudFormation): dormant
Lambda's `TargetTable=mint`, `Image404=https://i.stack.imgur.com/6M513.png`,
and repointed the `idn.prod.cloud.lib.vt.edu` CNAME to the dormant stack's
own CloudFront (`d23illvkjqb563.cloudfront.net`). Tested 100 random
`visibility=true` records from `Archive-ocrvf7v6rbdyrkx42edgadqo6u-production`
(`custom_key` → `http://idn.lib.vt.edu/<custom_key>`, sampled via 8-segment
parallel `dynamodb scan`).

- **Functional**: 69/100 → `digital.lib.vt.edu`, 8/100 → `iawa.lib.vt.edu`
  (legitimate federated-collection records), 23/100 → 404 fallback. Traced
  the 23 to a **pre-existing bug** — those `mint` records are missing the
  `hits` attribute, and both stacks' shared Lambda code fails identically on
  them (confirmed via direct curl to both API Gateways). Unrelated to the
  migration.
- **Routing: traffic had NOT moved.** CloudWatch showed 100/100 test
  invocations still on the legacy Lambda, 0 on the dormant one (apart from
  earlier manual probes). Root cause: CloudFront selects the serving
  distribution by matching SNI/Host against a distribution's registered
  Alternate Domain Names, not by the DNS CNAME chain used to reach an edge
  IP — so repointing the CNAME had no effect on real traffic. The dormant
  distribution had no alias registered; the unidentified front-door
  distribution (`d3btzx4iv66c21.cloudfront.net`) still held the alias and
  still pointed at the legacy API.

## Second verification pass — cutover confirmed

User identified that `d3btzx4iv66c21.cloudfront.net` was never a separate
customer account's distribution — it's the CloudFront distribution API
Gateway auto-provisions for an **edge-optimized Custom Domain Name**.
`idn.lib.vt.edu` was configured as a Custom Domain Name directly in API
Gateway (account `196766403141`), which is why it never surfaced in
`list-distributions` for any account checked. The user repointed that
Custom Domain Name's **base-path mapping** from the legacy API
(`ltghm34375`) to the dormant/mint-backed API (`zjxfzd5xih`).

Re-ran the identical 100-record test against `http://idn.lib.vt.edu/...`:

- **Functional**: identical results to the first pass (69/8/23 split) —
  confirming no behavior change from the cutover itself.
- **Routing: confirmed moved.** CloudWatch `AWS/Lambda Invocations` for the
  exact 1-minute test window showed **99 invocations on the formerly-dormant
  Lambda** (0 errors) and **0 on the legacy Lambda**. Cross-checked API
  Gateway request metrics and re-confirmed the dormant Lambda's env vars
  were unchanged and correct.

**Conclusion: the migration's cutover step is done.** Real `idn.lib.vt.edu`
production traffic is now served by the formerly-dormant stack. The
CNAME/DNS-based approaches in the original plan (repoint CNAME to own
CloudFront, or to the mystery CloudFront's account) were both dead ends —
the actual lever was API Gateway's own custom-domain base-path mapping.

## Third verification pass — `hits`-attribute bug fixed

User applied a Lambda code fix (the `hits`-increment logic now creates the
attribute if missing, instead of failing when it's absent). Re-ran the
identical 100-record test:

- **100/100 now resolve** — 91/100 → `digital.lib.vt.edu`, 9/100 →
  `iawa.lib.vt.edu`, 0/100 fall back to the 404 image (down from 23/100).
- All 23 previously-failing ark IDs individually confirmed now resolving.
- Spot-checked `mint` records directly: previously-missing `hits` attribute
  now present (`hits: "1"`), created as a side effect of the fixed
  increment logic on a normal resolve call — a code fix, not a data
  backfill.

## Open threads (see handoff.md for detail)

- **`dlp-services` CloudFormation stack drift**: declared parameters still
  say `NSTableName=dlp_minter` (stack is `UPDATE_ROLLBACK_COMPLETE` from a
  failed update attempt), but the Lambda's live config was fixed directly,
  out-of-band. A future stack update/redeploy would silently revert the fix
  unless reconciled.
- ~~The `hits`-attribute bug~~ — fixed, see above.
- **Decommissioning**: the legacy stack (`VTDLP-Resolution-Service`, API
  `ltghm34375`) is now receiving 0 traffic and can be torn down after a
  burn-in period; the dormant stack's own CloudFront (`E36QWU4GGFDPFY`) was
  never used for the cutover and is also a decommission/cleanup candidate.
- Colon-in-ark-path 403 quirk from the original inventory session was never
  reproduced in either verification pass's testing — status unclear, not
  re-investigated, likely moot now.
- Dormant Lambda IAM role policy document still unread (permissions
  denied) — moot for the completed cutover, but worth confirming if the
  `dlp-services` stack drift gets reconciled via a CFN update.
