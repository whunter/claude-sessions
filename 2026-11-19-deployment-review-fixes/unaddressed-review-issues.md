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
  env). Not run end to end: the root app has no tests;
- #8 `readBackend`'s four SSM calls: now one `ssm get-parameters`, matched by
  name, naming every missing parameter. `ssm:GetParameters` is already in v2
  of `dlp-access-next-web-deploy`. Destroy's single `get-parameter` read is
  unchanged;
- #9 `requireBackend()` twice per command: the CLI now resolves the backend
  once, with `--production`, and passes it to `planFrontend` as `backend`;
- #10 stale `infra/cdk.context.json`: removed (already gitignored). A
  `cdk synth` of dev ran with no lookups and wrote no new one.

No review issues are left.
