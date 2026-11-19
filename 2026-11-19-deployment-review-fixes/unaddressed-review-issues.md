# Unaddressed code-review issues: `whunter/feature/add/deployment`

These are from the `/code-review` of the branch against
`vt-digital-libraries-platform/dlp-access-next:main` on 2026-11-18. None of
them has been checked against the code yet, so some may not hold up. Line
numbers come from the review and are as of `239e207`. Fixes 1–3 have moved
lines in `deploy.ts` and `frontend.ts` since then.

Fixed this session, and not repeated here:
- #1 DNS record after an interrupted first deploy;
- #2 lifecycle policy tied to one backend's service role;
- #3 exact platform version pin;
- #7 duplicate SSM read in `ensureApplication`.

## Likely bugs

### 4. `--branch X` while on branch Y ships Y's HEAD as X

`infra/lib/frontend/frontend-cli.ts:213`

The commit is `git rev-parse HEAD`, but the version label (`<slug>-<sha>`), its
description ("commit <sha> of X") and the target environment all come from
`--branch`. On a redeploy, `eb deploy` ships the checked-out HEAD to
`dlpnext-X`. The tag check passes, because it compares only the `--branch`
value. Nothing warns.

Possible fix:
- refuse when `--branch` differs from the current branch and HEAD isn't the
  tip of X (`git rev-parse X`);
- or allow it only on a detached HEAD, the case `--branch` exists for, as in CI.

### 5. `frontend:status` ignores the backend's region

`infra/lib/frontend/frontend-cli.ts:149`

Status always queries `FRONTEND_REGION`, while deploy and destroy use the
backend env's region. `planFrontend` never checks that the two match, although
the `web.ts` comment says a frontend can only attach to a backend in that
region. Every env is currently `us-east-1`, so nothing breaks today. A backend
in another region would make status say "not deployed".

Possible fix: refuse a backend env outside `FRONTEND_REGION` in
`planFrontend`.

### 6. Logout can fail before clearing the session cookie

`src/app/auth/logout/route.ts:7`

The route awaits OIDC discovery (`getClient()`) before building the response
that expires `dlp_id_token`. If discovery fails or is slow, or
`end_session_endpoint` is missing, the user gets a 500 and stays signed in
until the ID token expires.

Possible fix: clear the cookie in all cases. If discovery fails, redirect to
`/` (or the app's base URL) instead of the Cognito logout endpoint.

## Cleanups

### 8. `readBackend` makes four sequential SSM calls

`infra/lib/frontend/deploy.ts` (`readBackend`)

Each `aws ssm get-parameter` starts a new CLI process (about 1–2 s each). One
`ssm get-parameters --names a b c d` would do, with `InvalidParameters` used
to report the missing ones. Note that `ssm:GetParameters` is a separate IAM
action from `ssm:GetParameter` (see the hand-off).

### 9. `requireBackend()` runs twice per command

`infra/lib/frontend/frontend-cli.ts:209`

`planWithRunner` resolves the backend env to get the region, then
`planFrontend` resolves it again, with different production arguments.
`planFrontend` could take the already-resolved config, or the runner could be
built from `plan.region`.

### 10. Stale `infra/cdk.context.json`

It is a cached `HostedZone.fromLookup` result from the removed Web stack.
Nothing in the backend-only CDK app reads it. It also commits AWS account ID
226388486048, against the "no account ID is stored here" intent in `web.ts`.
Delete it, and check that `cdk synth` writes nothing new back.
