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
- #7 duplicate SSM read in `ensureApplication`;
- #4 `--branch X` while on branch Y: verified, and `frontend:deploy` now
  refuses a `--branch` that differs from the checked-out branch (a detached
  HEAD, as in CI, still passes);
- #5 `frontend:status` ignores the backend's region: verified as latent (a
  test pinned the named envs to `FRONTEND_REGION`, but nothing enforced it).
  `planFrontend` now refuses a backend env outside `FRONTEND_REGION`;
- #6 logout failing before clearing the session cookie: verified. The route
  now always clears `dlp_id_token`, and redirects home when Cognito's logout
  URL can't be built (discovery failure, no `end_session_endpoint`, missing
  env). Not run end to end: the root app has no tests.

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
