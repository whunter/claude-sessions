# Session summary: Cognito sign-in for dlp-access-next (2026-10-02)

Worked in `~/dev/dlp/access/dlp-access-next-cdk` on branch `whunter/feature/cognito-auth`. Five commits, not pushed. Nothing was deployed and no Cognito resource was changed by the session.

## Goal

Put the `/examples/appsync-queries` page behind Cognito sign-in, limited to the `admin` group, starting from the NodeJS example on the Cognito console's quick-setup page. Then make the CDK app provide the user pool, app client and federated provider per environment.

## What happened

### 1. Protecting the page (`43ac2d7`)
- Read the NodeJS example from the console's quick-setup guide in Chrome (Express, `express-session`, `openid-client` 5.x).
- Ported it to Next route handlers: `/auth/login`, `/auth/callback`, `/auth/logout`, with `src/lib/auth.ts`. Kept `openid-client` 5.x; added `jose`.
- Session is the ID token in an httpOnly cookie, verified against the pool's keys per request. The group check reads `cognito:groups` from the ID token, because `userinfo` (which the example uses) has no groups.
- The page redirects to login or shows "Access denied"; the `searchCatalog` server action repeats the check.
- The example's logout host did not resolve (the pool has a custom domain), so logout uses the discovery document's `end_session_endpoint`.
- Created `.env.local` (already git-ignored by `.env*`).

### 2. Auth stack and per-branch app client (`52bfe19`)
- Added `DlpAccessNext-<env>-Auth`: a new pool, or `-c userPool=<id>` to use an existing one untouched. The pool ID goes to SSM, like the API URL, so Web stacks attach by name.
- Each Web stack creates its own confidential app client and sets the `COGNITO_*` variables on Beanstalk. The client is per branch because callback URLs belong to a deployment.
- Added `-c appUrl=https://<host>`: Cognito rejects non-localhost `http` callbacks and Beanstalk is HTTP only, so by default only `http://localhost:3000` is registered.

### 3. Shared app client question
- Asked whether a branch could add its callback URL to an existing client instead. Answer: possible only with a custom resource (read-modify-write, races, cleanup, 100-URL limit), and currently pointless because every branch's only callback is the same localhost URL.
- Proposed `-c userPoolClient=<client ID>` with hand-managed URLs. Not built; no decision yet.

### 4. Federated provider (`2bafb95`, `495e762`)
- The app always signs in through a federated provider (`VT-SSO-OIDC` on the existing pool). Added `-c identityProvider=<name>`: recorded in SSM, the branch's client allows only that provider, and the app passes it as `identity_provider`.
- Then made the Auth stack create the provider on a new pool from `-c identityProviderClientId` and `-c identityProviderSecret` (a Secrets Manager secret name, so the secret stays out of the template), with the issuer defaulting to VT SSO. Scopes and attribute mapping were copied from the existing provider's non-secret fields.
- The deploy confirmation prints the redirect URI that VT SSO has to allow.

### 5. Local sign-in
- Confirmed the localhost callback and sign-out URLs, and that Cognito has no wildcard or any-port matching.
- Renamed the callback route to `/authorize` to match the other entries on the app client (`2d9ba20`). The login cookie's path had to widen from `/auth` to `/` for the new route to see it.
- Filled the empty `COGNITO_CLIENT_SECRET` in `.env.local` from `aws cognito-idp describe-user-pool-client` without printing it, started `next dev` on port 3000 and opened the page in Chrome. Sign-in went through VT SSO on the existing browser session and the page rendered as an admin user.
- Looked up the Amplify `gentwo` API endpoint and the CDK dev API's tables (seven `<Model>-dlpnext-dev` tables, all reporting 0 items, plus the `dlpnext-dev` domain), then added the dev API URL to `.env.local`.

## Mistakes and corrections

- The first check of the route rename ran against a stale build: a leftover `.next` type file failed `tsc`, which skipped the rebuild in the same command. Rebuilt and re-verified.
- A first version of logout used the console example's domain through a `COGNITO_DOMAIN` variable; replaced with the discovered endpoint and the variable was dropped.

## State at the end

- Infra Jest: 114 tests pass. App: typecheck, lint and build pass.
- Not deployed, not pushed. Open items are listed in `handoff.md`.
