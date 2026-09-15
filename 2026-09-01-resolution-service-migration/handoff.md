# Hand-off: resolution-service-migration

**Goal:** Migrate `idn.lib.vt.edu` ark-resolution traffic from the live legacy
stack (`VTDLP-Resolution-Service`) to the dormant `dlp-services-ResolutionServiceApp`
stack, with no behavior change and no downtime. Builds on
`../2026-09-01-resolution-service-inventory/` which identified the two stacks.

## What's done

Investigated the open threads from the inventory session and produced a full
migration plan (written to `plan.md` in this directory). Key facts established:

1. **The dormant stack's backing DynamoDB table doesn't exist.** Its Lambda's
   `TargetTable` env var is `dlp_minter`, driven by the `dlp-services` parent
   stack's `NSTableName` parameter. `dlp_minter` is declared in that stack's
   template (as `MintServiceApp`'s `ResolutionTable` resource, physical name
   `dlp_minter`) but `aws dynamodb describe-table --table-name dlp_minter`
   returns `ResourceNotFoundException` — deleted out-of-band, stack never
   reconciled. `dlp-services` has been `CREATE_COMPLETE` since 2021-11-18 with
   no updates since; both its nested apps (Mint + Resolution) show 0 Lambda
   invocations in the trailing 30 days. This is why the dormant API currently
   returns the 404-fallback image for every request — not staleness, a missing
   table.
2. **`vtdlp_resser_idn`** (a table name that looked like a candidate) is a
   separate, much smaller table: 2,520 items vs. `mint`'s 40,194, not owned by
   either resolution CFN stack. Not a viable target without a full backfill
   from `mint` anyway — recommendation is to skip it and point the dormant
   stack directly at `mint`.
3. **The real front door is a DNS CNAME, not fixed infra**:
   `idn.prod.cloud.lib.vt.edu` → `d3btzx4iv66c21.cloudfront.net` (TTL 300s).
   The owning AWS account for that CloudFront distribution is still
   unidentified (checked `196766403141` and `226388486048`/`eb-cli`; absent
   from both). Rather than needing access to that unknown account, the plan
   instead repoints the CNAME to one of *our* CloudFront distributions
   (the dormant stack's own `E36QWU4GGFDPFY` / `d23illvkjqb563.cloudfront.net`),
   bypassing the mystery front door entirely.
4. Confirmed the two stacks' own CloudFront distributions
   (`E2CZDTXELAYPFI` live / `E36QWU4GGFDPFY` dormant) have **identical**
   default cache behavior (TTL 0, no query-string/cookie forwarding, only the
   `Origin` header forwarded) — they're clones from the same SAR
   ("NameResolutionService" v1.0.4) template, so relative to each other there's
   no caching-behavior drift to worry about.
5. Neither of those two CloudFronts currently has any alternate domain name
   (`Aliases: null` on both) — neither is set up to directly serve
   `idn.lib.vt.edu` today. An ACM cert for `idn.lib.vt.edu` does already exist
   in `196766403141` (`us-east-1`, usable by CloudFront).

## Verification pass (after user applied the backend fix)

The user repointed the dormant Lambda directly (not via CloudFormation — see
drift note below) to `TargetTable=mint`, `Image404=https://i.stack.imgur.com/6M513.png`,
and changed the `idn.prod.cloud.lib.vt.edu` CNAME to the dormant stack's own
CloudFront (`d23illvkjqb563.cloudfront.net`). Verification tested 100 random
`visibility=true` records from `Archive-ocrvf7v6rbdyrkx42edgadqo6u-production`
(sampled via 8-segment parallel `dynamodb scan`, `custom_key` field →
`http://idn.lib.vt.edu/<custom_key>`).

**Functional result:** 69/100 resolved to `digital.lib.vt.edu`, 8/100 resolved
to `iawa.lib.vt.edu` (a different, legitimate VT digital-library site — those
are federated-collection records, not a bug), 23/100 fell back to the 404
image. Checked several of the 23 failures directly in `mint` via
`get-item` — the records exist with valid `long_url` values but are all
**missing the `hits` attribute** that working records have. Confirmed via
direct `curl` to both `ltghm34375` (legacy) and `zjxfzd5xih` (formerly
dormant) API Gateways with the same failing ark IDs: **both stacks fail
identically**, since they run the same Lambda code. This is a **pre-existing
bug unrelated to the migration** — worth a separate ticket (the Lambda likely
does an `UpdateItem` to increment `hits` using an expression that assumes the
attribute already exists, and its broad exception handling masks the error as
"not found") — but it does not block or get introduced by the migration.

**Cutover result — traffic has NOT actually moved yet.** This is the
important correction to the plan (`plan.md` step 5). Running the 100-record
test through `http://idn.lib.vt.edu/...` produced **100 invocations on the
legacy Lambda** (`VTDLP-Resolution-Service-NameResolutionFunction-...`) in
CloudWatch, and only the handful of invocations on the dormant Lambda that
matched manual direct-API-Gateway probes made earlier in the session — zero
from the batch test. So despite the DNS CNAME being changed, real
`idn.lib.vt.edu` traffic is still being served by the legacy stack.

**Root cause: the CNAME-repoint approach in `plan.md` doesn't work.**
CloudFront selects which distribution serves an HTTPS request by matching the
TLS SNI / `Host` header against whichever distribution has that hostname
registered as an **Alternate Domain Name (alias)** — not by which CNAME chain
DNS used to reach an edge IP (CloudFront's edge IP pool is shared/anycast
across all distributions, so resolving to a particular distribution's own
`*.cloudfront.net` domain doesn't mean that distribution handles the request).
The dormant stack's own distribution (`E36QWU4GGFDPFY`) has `Aliases: null` —
no alias registered — so SNI=`idn.lib.vt.edu` still gets claimed by whichever
distribution *does* have that alias registered, which is still the
unidentified front-door distribution (`d3btzx4iv66c21.cloudfront.net`), still
pointed at the legacy API Gateway. **There is no DNS-only trick that avoids
needing write access to that unidentified account** — the actual cutover
requires either changing that distribution's origin, or moving its
`idn.lib.vt.edu` alias onto the dormant distribution (aliases are globally
unique across CloudFront, so both changes require access to the account that
currently owns it).

**Practical upshot (at the time):** no production risk from that first backend
change — real users were still being served by the proven legacy stack
throughout. But the migration wasn't done until the actual front door was
found and repointed — see the cutover confirmation below.

## Cutover confirmed (second verification pass)

The "unidentified front-door CloudFront account" mystery is resolved: it was
never a separate customer account. `d3btzx4iv66c21.cloudfront.net` is the
distribution API Gateway auto-provisions for an **edge-optimized Custom
Domain Name** — `idn.lib.vt.edu` was configured as a Custom Domain Name
directly in API Gateway (in `196766403141`), with a base-path mapping
pointing at the live API's stage. That CloudFront distribution lives in an
AWS-managed account outside customer visibility, which is why
`list-distributions` never found it in either account checked. The fix was
to repoint the **base-path mapping** (not DNS, not raw CloudFront) from the
legacy API `ltghm34375` to the dormant/mint-backed API `zjxfzd5xih`.

Re-ran the same 100-record test (`custom_key` field from
`Archive-ocrvf7v6rbdyrkx42edgadqo6u-production`, `visibility=true`) through
`http://idn.lib.vt.edu/...` after that remapping:

- **Functional result: identical to the first pass** — 69/100 →
  `digital.lib.vt.edu`, 8/100 → `iawa.lib.vt.edu`, 23/100 → 404 fallback
  (the pre-existing `hits`-attribute bug, unaffected by this change).
- **Traffic routing: confirmed moved.** CloudWatch `AWS/Lambda Invocations`
  for the exact 1-minute window the batch ran (`2026-09-01T22:15:00Z`) shows
  **99 invocations on the formerly-dormant Lambda**
  (`dlp-services-ResolutionServ-NameResolutionFunction-1ttBuMQ1rMrp`, 0
  errors) and **0 on the legacy Lambda**
  (`VTDLP-Resolution-Service-NameResolutionFunction-...`). This is the
  opposite of the first verification pass, which found 100/100 still hitting
  legacy — the base-path-mapping change is what actually did it.
- Dormant Lambda's env vars re-checked and still correct:
  `TargetTable=mint`, `Image404=https://i.stack.imgur.com/6M513.png`.
- Note: the dormant stack's *own* CloudFront (`E36QWU4GGFDPFY`) still has
  `Aliases: []` — it was never used for the cutover and can be considered
  dead weight now, since routing goes through API Gateway's custom-domain
  CloudFront, not either stack's own SAR-provisioned one.

**The `idn.lib.vt.edu` CNAME and DNS chain were never the actual lever** —
`plan.md` step 5 (repoint the CNAME) and the earlier "repoint to our own
CloudFront" idea were both dead ends. The real cutover step is: update the
API Gateway Custom Domain Name's base-path mapping.

### Current infra split (post-cutover)

| | Now serving `idn.lib.vt.edu` traffic | No longer relevant to the live path |
|---|---|---|
| CloudFront | `d3btzx4iv66c21.cloudfront.net` (API Gateway-managed, custom domain `idn.lib.vt.edu`) | `E2CZDTXELAYPFI` (legacy stack's own CF) / `E36QWU4GGFDPFY` (dormant stack's own CF, unused, no alias) |
| API Gateway | `zjxfzd5xih` (base-path mapping target) | `ltghm34375` (legacy, still deployed, receiving 0 traffic) |
| Lambda | `dlp-services-ResolutionServ-NameResolutionFunction-1ttBuMQ1rMrp` | `VTDLP-Resolution-Service-NameResolutionFunction-1IZLCRWFTW5NY` (idle) |
| DynamoDB | `mint` | — (shared table, unchanged) |

## Third verification pass — `hits`-attribute bug fixed

User applied a Lambda code fix (the increment logic now creates the `hits`
attribute if missing instead of failing when it's absent, e.g.
`SET hits = if_not_exists(hits, :zero) + :incr` in place of an expression
that assumed the attribute already existed). Re-ran the identical 100-record
test against `http://idn.lib.vt.edu/...`:

- **100/100 now resolve** — 91/100 → `digital.lib.vt.edu`, 9/100 →
  `iawa.lib.vt.edu`, **0/100 fall back to the 404 image** (down from 23/100).
- Checked all 23 previously-failing ark IDs individually — every one now
  resolves correctly.
- Spot-checked the underlying `mint` records directly via `get-item`
  (e.g. `7d957035`, `608e85b2`, `37e91d68`): each now has `hits: "1"`,
  where the attribute was absent before. This is the fixed increment logic
  creating the attribute as a side effect of a normal resolve request, not
  a manual data backfill — consistent with a code fix rather than a data
  patch.

The `hits`-attribute bug (open thread #2 below) is resolved.

### New drift risk found during verification

The `dlp-services` CloudFormation stack is in `UPDATE_ROLLBACK_COMPLETE`
(an update attempt at 2026-09-01T18:05:27Z failed and rolled back), but the
dormant Lambda's live configuration already shows the fixed values
(`TargetTable=mint`, `Image404=...i.stack.imgur.com...`) — meaning the fix was
applied directly to the Lambda (console/CLI), not through CloudFormation. The
stack's declared parameters still say `NSTableName=dlp_minter` and the old
`Image404`. **Any future stack update or redeploy will silently revert the
Lambda to the broken `dlp_minter` config** unless this drift is reconciled
(re-run the parameter update to `mint` so it actually succeeds, or otherwise
bring the stack's declared state in line with reality).

## What's NOT done / open threads

**Cutover itself is done and confirmed** (see above) — the remaining items
are cleanup, drift reconciliation, and pre-existing bugs, not blockers to
production traffic already being on the new stack.

1. **The `dlp-services` stack drift** (declared `NSTableName=dlp_minter` in
   CloudFormation, actual Lambda config `mint`, applied out-of-band) needs
   reconciling so a future stack update doesn't silently revert the fix — see
   the drift note above.
2. ~~**The `hits`-attribute bug**~~ — **Fixed** (see third verification pass
   above). Was a Lambda code issue (increment expression failed when `hits`
   was absent); now self-heals the attribute on resolve. Confirmed via
   re-test: 0/100 fallbacks, down from 23/100.
3. **Decommission candidates, now that cutover is confirmed:** the legacy
   stack (`VTDLP-Resolution-Service` — API `ltghm34375`, Lambda, CloudFront
   `E2CZDTXELAYPFI`) is receiving 0 traffic and can be torn down after a
   burn-in period; the dormant stack's *own* CloudFront
   (`E36QWU4GGFDPFY`/`d23illvkjqb563.cloudfront.net`) was never used for the
   cutover (routing goes through API Gateway's custom-domain CloudFront
   instead) and could also be removed or repurposed.
4. **The colon-in-ark-path 403 quirk** noted in the original inventory
   session was never reproduced during either verification pass's 100-record
   tests (all failures were the `hits`-attribute 404-fallback, not a 403 at
   the `idn.lib.vt.edu` layer) — status unclear/likely moot now, not
   re-investigated.
5. **Permissions gap** (`apigateway:GET`, `route53:List*`,
   `iam:GetRolePolicy`, etc. denied to `vtdlp-whunter-workload`) meant the
   API Gateway custom-domain/base-path-mapping config that turned out to be
   the actual lever couldn't be read directly this session — confirmed only
   indirectly via CloudWatch invocation counts and your description of the
   change. Worth granting `apigateway:GET` for future audits of this kind.

## Key commands used (reusable for future audits/execution)

```sh
aws lambda get-function-configuration --function-name <name> --query 'Environment.Variables'
aws dynamodb describe-table --table-name <name>
aws dynamodb list-tables
aws cloudformation describe-stacks --stack-name <name> --query 'Stacks[0].Parameters'
aws cloudformation list-stack-resources --stack-name <name>
aws iam list-role-policies / list-attached-role-policies --role-name <name>
aws acm list-certificates --query 'CertificateSummaryList[].DomainName'
aws cloudfront get-distribution --id <id> --query 'Distribution.{Domain:DomainName,Aliases:...,Origin:...}'
aws cloudfront get-distribution --id <id> --query 'Distribution.DistributionConfig.DefaultCacheBehavior'
dig idn.prod.cloud.lib.vt.edu CNAME +noall +answer
```

Denied but would help if granted: `apigateway:GET`, `route53:List*`,
`iam:GetRolePolicy`, `tag:GetResources`, plus write access
(`cloudformation:UpdateStack`, `iam:PutRolePolicy`,
`cloudfront:UpdateDistribution`) to actually execute the migration.

See `plan.md` in this directory for the full step-by-step migration plan.
