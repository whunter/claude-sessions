# Handoff: remove Cognito user pool provisioning (dlp-access-next-cdk)

Repo: `~/dev/dlp/access/dlp-access-next-cdk`, branch `whunter/feature/remove/cognito`, 2 commits on top of `2d9ba20`, **pushed** to origin. No pull request is open. Nothing was deployed and no AWS resource was changed.

Follows the 2026-10-02 session (`../2026-10-02-cognito-auth/`), which added the Auth stack and sign-in.

## What changed

| Commit    | Change                                                                                               |
| --------- | ---------------------------------------------------------------------------------------------------- |
| `904ede9` | The Auth stack no longer provisions a user pool; `-c userPool` is required for an environment deploy |
| `2d28cfb` | Stale comment in `lib/web-stack.ts`                                                                  |

### Infra (`infra/`)

- `lib/auth-stack.ts`: only writes the two SSM parameters (`/dlp-access-next/<env>/user-pool-id`, `/dlp-access-next/<env>/identity-provider`) and the `UserPoolId` and `IdentityProvider` outputs. The pool, `admin` group, managed login domain and OIDC provider resources are gone, as are the `ManagedLoginUrl` and `IdentityProviderRedirectUri` outputs and the `ADMIN_GROUP` export. The prop is `userPoolId` (required), formerly `existingUserPoolId`.
- `lib/app.ts`: `planApp` throws "Missing CDK context: pass -c userPool=<user pool ID>" when the environment's stacks are in the app (no `-c branch`, or `-c backend=provision`) and `userPool` is missing. It is still rejected on an attach deploy. Removed `identityProviderClientId`, `identityProviderSecret`, `identityProviderIssuer`, `planOidcProvider` and `AppPlan.oidcProvider`.
- `lib/environments.ts`: removed `OidcProviderConfig`, `DEFAULT_OIDC_ISSUER`, `managedLoginDomainPrefix`, `identityProviderRedirectUri`.
- `lib/deploy.ts`: the confirmation shows the pool ID (or "(the environment's)" on attach); the "Provider redirect" row is gone.
- `lib/web-stack.ts`: unchanged apart from a comment. Each Web stack still creates its own confidential app client on the environment's pool and sets `COGNITO_ISSUER`, `COGNITO_CLIENT_ID`, `COGNITO_CLIENT_SECRET` and `COGNITO_IDENTITY_PROVIDER`.
- Tests: `userPool` added to every environment-deploy case; the provisioning and OIDC tests were removed; a new case checks that a missing `userPool` is rejected. 104 Jest tests pass, `npx tsc --noEmit` is clean.
- `README.md` and `CLAUDE.md` describe the new options.

The root Next.js app was not touched.

## Decisions

- `-c userPool` is required rather than optional. This was the assistant's choice, not discussed beforehand: without an Auth stack the SSM parameters would not exist and every Web stack for the environment would fail to deploy.
- `-c identityProvider` stays optional and defaults to `COGNITO` (the pool's own users). Leaving it off a later environment deploy resets the environment to `COGNITO`.

## Before deploying

- No environment's Auth stack is known to have been deployed with a CDK-provisioned pool (nothing was deployed in the 2026-10-02 session either). If one was, the next deploy removes the pool's group, domain and OIDC provider from the stack. In `dev`, `pre-production` and `production` the pool itself is retained but orphaned; in an `f-` environment it is deleted. Check with `aws cloudformation list-stack-resources --stack-name DlpAccessNext-<env>-Auth` first.
- Web stacks attached to an environment keep their app client on the old pool until they are redeployed.
- The existing pool needs its own managed login domain, `admin` group and (if used) federated provider; CDK changes none of them.

## Commands

```bash
cd infra
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
npm run deploy -- -c env=dev -c account=$ACCOUNT -c userPool=<user pool ID> -c identityProvider=VT-SSO-OIDC
npm run deploy -- -c env=dev -c account=$ACCOUNT -c branch=$(git branch --show-current)
```

## Next steps

- Open a pull request for `whunter/feature/remove/cognito` into `main`.
- Sign-in still works only on `localhost:3000` until the Beanstalk environments have HTTPS in front of them (`-c appUrl`), as before.
