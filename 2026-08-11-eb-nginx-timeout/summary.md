# Session: Elastic Beanstalk nginx timeout on form submission

**Date:** 2026-08-11
**Repo:** `dlp-ingest` (branch `dev`)
**Goal:** Determine whether the config added in commit `feaf2bf` ("fix timeout") actually fixes nginx timeouts (<10 min) on the form submission page, for a load-balanced EB environment.

## Starting point

Commit `feaf2bf` added two files:

- `.platform/nginx/conf.d/timeout.conf` — sets `proxy_connect_timeout`, `proxy_send_timeout`, `proxy_read_timeout`, `send_timeout` to 600 on the instance-local nginx.
- `.ebextensions/network.config` — set `aws:elasticbeanstalk:command` / `Timeout` to 600.

Platform: Python 3.13 on 64-bit Amazon Linux 2023 (`.elasticbeanstalk/config.yml`), branch `dev` → environment `dlp-ingest-pprd`. App runs via gunicorn (`Procfile`), confirmed load-balanced (defaults to an ALB on the EB Python platform).

## Findings

- `.platform/nginx/conf.d/timeout.conf` is correct and necessary — it covers the instance-local nginx-to-gunicorn proxy hop.
- `.ebextensions/network.config`'s original setting (`aws:elasticbeanstalk:command Timeout`) was a **no-op for this problem**: that namespace controls how long EB waits during *deployments*/health-check-wait, not request-handling timeouts. It doesn't touch the live HTTP path at all.
- Two gaps existed that neither file addressed, both of which matter more than what was committed:
  1. **Gunicorn worker timeout** — `Procfile` had `--timeout 120`. Gunicorn kills and restarts any worker still handling a request past that, independent of nginx's timeout, so anything over 2 minutes would fail at the app-server layer regardless of the nginx config.
  2. **ALB idle timeout** — because the environment is load-balanced, traffic goes client → ALB → instance nginx → gunicorn. The ALB has its own idle timeout (60s default) that is entirely separate from instance-level nginx config, and would return its own 504 before the instance was ever involved.

## What was changed

1. `Procfile` — gunicorn `--timeout` raised from `120` to `600` to match nginx.
2. `.ebextensions/network.config` — replaced the ineffective `aws:elasticbeanstalk:command Timeout` entry with `aws:elbv2:loadbalancer` / `IdleTimeout: 600` (the user edited this directly mid-session to drop the old entry rather than keep both).

End state: all three tiers in the request path (ALB, nginx, gunicorn) aligned at a 600s timeout.

## State at end of session

- `Procfile` and `.ebextensions/network.config` modified, not committed (`git status`: `M Procfile`, `M .ebextensions/network.config`).
- No commit was made — not requested.
- No deploy was run.
