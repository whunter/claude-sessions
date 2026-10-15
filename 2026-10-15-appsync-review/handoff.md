# Hand-off: appsync-review (2026-10-15)

**Repo:** `~/dev/dlp/access/dlp-access-next-cdk`, branch `whunter/appsync` (clean, last commit `348cb93`)

## State

All code-review-fix tickets (01–06) are implemented. Only ticket 05 is still open. It needs a check by a person on a deployed stack.

## Next steps

1. Deploy the dev Web stack (you run this; it asks for confirmation):
   ```
   cd infra
   ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
   npm run deploy -- -c env=dev -c account=$ACCOUNT -c branch=$(git branch --show-current)
   ```
2. Check sign-in. Beanstalk serves only HTTP, and Cognito accepts HTTP callbacks only for localhost. So without HTTPS in front of the app and `-c appUrl`, test sign-in locally on `localhost:3000`:
   - Use the Web stack outputs `CognitoIssuer`, `CognitoClientId` and `CognitoIdentityProvider`.
   - Get the secret with `aws secretsmanager get-secret-value --secret-id <CognitoClientSecretArn> --query SecretString --output text`.
   - Also check that the Beanstalk configuration shows `COGNITO_CLIENT_SECRET` only as a secret ARN under `aws:elasticbeanstalk:application:environmentsecrets`.
3. If sign-in works, check off the remaining item in `.scratch/code-review-fixes/issues/05-cognito-client-secret-out-of-plaintext.md`, set `Status: done`, and commit.
4. Optional: update or remove the stale `ready-for-agent` label in `docs/issues/multi-env-data-layer.md`.

## Known caveats (from ticket 05)

- Every branch of an environment shares that environment's instance role, so the branches can read each other's client secrets.
- The secret has no resource policy.
- Replacing the app client changes `COGNITO_CLIENT_ID`, which should update the environment. This hasn't been tested.
