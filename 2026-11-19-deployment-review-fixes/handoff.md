# Hand-off: deployment branch review fixes (dlp-access-next-cdk)

## State

- Branch `whunter/feature/add/deployment`, head `58ac0e4`. It is **3 commits
  ahead of origin, not pushed**. The working tree is clean.
- Tests pass: `cd infra && npx tsc --noEmit -p . && npx jest` (261).
- Nothing was deployed. The only AWS calls were read-only:
  `list-available-solution-stacks`, `list-platform-versions`, and a
  `findSolutionStack` run as the IAM user.

## Commits this session

- `ea459f5` Redeploy writes the DNS record and waits for a pending environment
- `bd207c4` Move the lifecycle policy off a destroyed backend's service role
- `58ac0e4` Create frontends on the platform branch's newest version

## Next steps

1. Decide whether to push these three commits.
2. Work through `unaddressed-review-issues.md`. #4 (`--branch` ships the wrong
   commit) is the most likely to hurt someone. It also affects the redeploy
   path changed by fix 1.
3. Not yet verified on AWS:
   - redeploying an environment that is still `Launching`;
   - the lifecycle policy moving off a destroyed `f-` backend's role.

   Both are covered only by the fake runner.

## Things to know

- `ensureApplication(serviceRoleArn, solutionStack, run)` and
  `initEbProject(solutionStack, run)` changed signature. `SOLUTION_STACK` no
  longer exists: use `PLATFORM_BRANCH` and `findSolutionStack`.
- A redeploy now also makes these calls:
  - `route53 list-hosted-zones-by-name`;
  - `route53 change-resource-record-sets` (UPSERT);
  - `elasticbeanstalk list-available-solution-stacks`.

  The IAM user's policy drafted for issue #6 covers the Route53 UPSERT, but it
  is still unconfirmed whether that policy is attached to the
  `vtdlp-access-deploy` group.

- The lifecycle repair needs `ssm:GetParameters`, which is a separate IAM
  action from `ssm:GetParameter`. It was added on 2026-11-19 as v2 (default)
  of the customer-managed policy `dlp-access-next-web-deploy`, still limited to
  `/dlp-access-next/*`. v1 is kept for rollback. A `get-parameters` call as the
  IAM user was checked and works.
