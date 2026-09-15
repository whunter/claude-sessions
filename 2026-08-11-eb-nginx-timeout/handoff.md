# Hand-off: Elastic Beanstalk nginx timeout on form submission

**Repo:** `dlp-ingest` (branch `dev`, environment `dlp-ingest-pprd`)

## Current state

- `Procfile` modified: gunicorn `--timeout` raised from `120` to `600`.
- `.ebextensions/network.config` modified: replaced the ineffective `aws:elasticbeanstalk:command Timeout` entry with `aws:elbv2:loadbalancer` / `IdleTimeout: 600`.
- Both changes are uncommitted (`M Procfile`, `M .ebextensions/network.config`); no deploy has been run.
- Prior commit `feaf2bf` had already added `.platform/nginx/conf.d/timeout.conf` (600s on the instance-local nginx), which was confirmed correct and left as-is.
- Full request path now aligned at 600s across all three tiers: ALB idle timeout, instance nginx, gunicorn worker timeout.

## Not yet done

- No commit made.
- No deploy performed — the fix has not been validated against the live `dlp-ingest-pprd` environment or a real long-running form submission.

## Next steps

1. Commit `Procfile` and `.ebextensions/network.config` on branch `dev`.
2. Deploy to `dlp-ingest-pprd` (`eb deploy` or the team's normal CI path) and confirm the ALB idle timeout setting actually took effect (check the target group / load balancer settings in the AWS console or via `aws elbv2 describe-load-balancer-attributes`).
3. Reproduce the original slow form submission (or a synthetic request that runs past 60s but under 600s) against the deployed environment to confirm no more 504s.
