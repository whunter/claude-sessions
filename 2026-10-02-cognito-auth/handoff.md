# Handoff: Cognito sign-in for dlp-access-next (dlp-access-next-cdk)

Repo: `~/dev/dlp/access/dlp-access-next-cdk`, branch `whunter/feature/cognito-auth`, 5 commits on top of `191ae2d`, **not pushed**. Nothing was deployed. No Cognito resource was changed from this session (the user added the localhost callback URL to the existing app client by hand).

Pool IDs, client IDs, API URLs and the account ID are deliberately not in this folder. The local values are in the repo's git-ignored `.env.local`.

## What changed

| Commit | Change |
|---|---|
| `43ac2d7` | `/examples/appsync-queries` requires Cognito sign-in and the `admin` group |
| `52bfe19` | New `DlpAccessNext-<env>-Auth` stack; each Web stack gets its own app client |
| `2bafb95` | `-c identityProvider=<name>`: sign in through a federated provider |
| `495e762` | The Auth stack can create the OIDC provider on a new pool |
| `2d9ba20` | Callback route renamed from `/auth/callback` to `/authorize` |

### App (root project)

- `src/lib/auth.ts`: OIDC authorization code flow with `openid-client` 5.x (as in the Cognito console's NodeJS example) plus `jose`. The session is the Cognito ID token in an httpOnly cookie (`dlp_id_token`), verified against the pool's JWKS on every request. No server-side session store.
- Routes: `/auth/login`, `/authorize` (callback), `/auth/logout`.
- `/examples/appsync-queries` redirects to login when signed out and shows "Access denied" when the user is not in `admin` (`cognito:groups` claim of the ID token). The `searchCatalog` server action repeats the check.
- Environment variables: `COGNITO_ISSUER`, `COGNITO_CLIENT_ID`, `COGNITO_CLIENT_SECRET`, optional `COGNITO_IDENTITY_PROVIDER` (sent as `identity_provider`, so sign-in skips managed login's chooser), optional `APP_BASE_URL`.
- Logout uses the `end_session_endpoint` from the pool's discovery document. The console example's logout host (custom domain with `.auth.<region>.amazoncognito.com` appended) does not resolve.

### Infra (`infra/`)

- `lib/auth-stack.ts`: per environment. Provisions a pool `dlpnext-<env>` (admin-created users, email sign-in, `admin` group, managed login domain `dlpnext-<env>-<account>`, retained except in `f-` environments), or with `-c userPool=<id>` only records an existing pool. Writes SSM parameters `/dlp-access-next/<env>/user-pool-id` and `/dlp-access-next/<env>/identity-provider` (`COGNITO` when there is no federated provider).
- `lib/web-stack.ts`: reads both parameters, creates a confidential app client (code flow, `openid email`, only the environment's identity provider, callbacks for `http://localhost:3000` and optionally `-c appUrl`), and sets the four `COGNITO_*` variables on the Beanstalk environment.
- New context options: `userPool`, `identityProvider`, `identityProviderClientId`, `identityProviderSecret` (Secrets Manager secret name, resolved by CloudFormation), `identityProviderIssuer` (defaults to VT SSO), `appUrl`. Validation is in `planApp` (`lib/app.ts`); the deploy confirmation shows them (`lib/deploy.ts`).
- The OIDC provider settings (scopes `openid email`, GET attribute requests, `email` and `username` from `sub`) were copied from the non-secret fields of `VT-SSO-OIDC` on the existing pool.
- `CLAUDE.md` and `README.md` document all of it.

## Verified

- Infra: typecheck and Jest pass (114 tests); full `cdk synth` succeeds with a new pool, a federated provider and a branch.
- App: typecheck, lint of `src` and `next build` pass.
- Local sign-in works end to end against the existing VT pool on `http://localhost:3000`: through VT SSO and back to the page as an `admin` member. It used the browser's existing VT SSO session, so no credentials were typed.

## Not verified

- Any deploy: the Auth stack, the per-branch app client, and OIDC provider creation have only been synthesized.
- Sign-out: the existing app client has no allowed sign-out URLs. `http://localhost:3000/` has to be added before the link works.
- The "Access denied" path with a real non-admin user.
- The queries page with data: the dev environment's tables report 0 items.

## Things to know before deploying

- **Existing Web stacks need the Auth stack first.** An attach deploy fails with "Unable to fetch parameters" until the environment's stacks are redeployed.
- **`-c userPool` and `-c identityProvider` must be passed on every environment deploy.** Leaving `userPool` off switches the environment to a newly provisioned pool.
- **Deployed sign-in needs HTTPS.** Cognito rejects `http` callbacks except localhost, and the Beanstalk environments are HTTP only. `-c appUrl=https://<host>` registers a public origin once there is one.
- **A new pool with VT SSO needs two manual steps first:** VT SSO must allow the pool's redirect URI (printed in the deploy confirmation as `Provider redirect`), and the client secret must be in Secrets Manager as plain text.
- **The client secret is a Beanstalk environment variable**, so it is visible in the Beanstalk configuration.
- **Federated users need adding to the `admin` group** in the pool after their first sign-in.
- **Cognito callback URLs match exactly, port included.** No wildcards.

## Open items

1. **Shared app client.** The user asked whether branches could reuse an existing client instead of creating one each. Proposed, not built: `-c userPoolClient=<client ID>` recorded by the Auth stack, Web stacks read its ID and secret, callback URLs managed by hand until branches have HTTPS origins. Awaiting a decision.
2. **Should `-c identityProvider` be required?** The user said the app will always use a federated provider; it is currently optional and falls back to the pool's own users.
3. **Garbled setup notice** in `src/app/examples/appsync-queries/page.tsx` (the amber "Set the APPSYNC_API_URL…" text). It predates this branch. Offered to fix; not done.
4. **Local state left behind:** `.env.local` (git-ignored) holds the issuer, client ID, client secret, identity provider and the dev API URL. A `next dev` server was left running on port 3000.
5. **Push** the branch when ready.
