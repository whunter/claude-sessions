# Session summary: web-stack (2026-09-24)

Repo: `dlp-access-next-cdk`, branch `whunter/multi-env`. This session continues `2026-09-24-data-layer-provision`, which built the per-environment Data and Api stacks.

## Goal

Add a separate CDK stack that deploys the Next.js app to Elastic Beanstalk. Whoever deploys chooses whether the app attaches to an existing environment's stacks (feature, dev, pre-production or production) or provisions new ones to support it.

## How it went

1. **Pushed** `whunter/multi-env` at the user's request (the data-layer commits).
2. **Looked at the existing Beanstalk setup** to copy it:
   - The hand-made `appsync-stack` environment runs on Node.js 24 on AL2023, as a single `t3.small` instance with enhanced health and managed minor updates.
   - The `.platform` prebuild hook runs `npm ci && npm run build`.
   - The PR-preview workflows build a Docker image from a Dockerfile the repo doesn't have, so they are probably stale.
3. **Built `DlpAccessNext-Web-<branch-slug>`** (commit `cf56eda`):
   - `-c branch=<git branch>` adds the Web stack.
   - `-c backend=attach` (the default) deploys only the Web stack. `-c backend=provision` also deploys the environment's Data and Api stacks, before it.
   - The Web stack finds its environment by fixed names, not by cross-stack references: the instance profile `dlp-access-next-<env>-eb`, and the SSM parameter `/dlp-access-next/<env>/graphql-api-url`, which the Api stack now writes. That's what lets it attach to stacks deployed on an earlier run.
   - The source bundle is an S3 asset of the repo root, minus `.gitignore` entries, `infra`, docs and `.env*`. File modes are kept, so the prebuild hook stays executable.
   - The stack has its own Beanstalk service role. IMDSv1 is disabled, logs stream to CloudWatch, and there is no SSH key pair and no open SSH rule.
   - Stale `DlpAccessNextAppSyncStack` references in the Next.js code and the demo page were updated.
   - Jest grew from 19 to 30 tests.
4. **First deploy failed:** the `AWSElasticBeanstalkEnhancedHealth` managed policy lives at `policy/service-role/...`. I fixed the ARN and added a regression test (`c2c4173`, 31 tests). The user redeployed:
   - dev's Data, Api and Web stacks are all `CREATE_COMPLETE`.
   - The EB environment `dlpnext-whunter-multi-env` is Ready / Green.
5. **Handoff** written. **README** rewritten from the create-next-app boilerplate into a project README covering environments, stacks, local run, deploy commands and tests (`c9e6b85`, not pushed).

## Decisions made without asking (flag if wrong)

- Each Web stack is keyed by branch alone (`DlpAccessNext-Web-<slug>`), not by branch and environment, so a branch has one deployment that can be repointed at another environment.
- The default backend is `attach`, because it can't create or change any data resources.
- Each Web stack owns its own Beanstalk application rather than sharing the existing `dlp-access-next` application.
- Web environments are single-instance and HTTP only: no load balancer, HTTPS or custom domain yet.
- The platform is pinned in `SOLUTION_STACK` (`v6.11.8`), with managed minor updates on.

## Open items

These are in `handoff.md`:
- Check the demo page on the new environment.
- Destroy the old `DlpAccessNextAppSyncStack`, and decide whether to retire the `appsync-stack` EB environment.
- Decide on HTTPS or a custom domain.
- Decide whether to point the PR-preview workflows at the Web stack.
- Deploy pre-production.
- Push `c9e6b85`, and open a PR only when asked.
