## Title of Pull Request(PR) [REQUIRED]
Add CDK infrastructure, AppSync API, and Cognito sign-in



## 🔗 Asana, 4Help, and Related Links [REQUIRED]
**Asana Ticket**: [Insert link]
**4Help Ticket (if applicable)**: N/A
**Other References**: `README.md` (options, local setup), `docs/deployment.md` (create / update / destroy commands, CI), `infra/schema/schema.graphql` (API source of truth)



## ✨ What Does This Pull Request Do?  [REQUIRED]
This is the first real PR on top of the bootstrap app. It defines all of the AWS infrastructure for dlp-access-next with CDK. Each backend environment (`dev`, `pre-production`, `production`, or a short-lived feature environment `f-<slug>`) gets its own DynamoDB tables, OpenSearch domain and AppSync API. Any git branch can deploy its own Elastic Beanstalk frontend against one of these environments, at `https://<branch>.dlp-access-dev.dlp.cloud.lib.vt.edu`, with VT SSO sign-in through Cognito.

This replaces depending on the Amplify app's resources: the data layer, search and API now live in this repo and can be stood up per environment.



## 🛠️ Summary of Changes [REQUIRED]
**`infra/` (new CDK v2 project), four kinds of stack:**
* `DlpAccessNext-<env>-Data`: seven DynamoDB tables (`<Model>-dlpnext-<env>`, same keys/GSIs as the vtdlpdev Amplify tables) and an OpenSearch 2.19 domain. Tier environments keep their tables (deletion protection + PITR); feature environments delete them on destroy.
* `DlpAccessNext-<env>-Api`: read-only AppSync API (IAM auth) with generated APPSYNC_JS resolvers, including full-text and filtered search (`fulltextArchives`, `fulltextCollections`, `searchObjects`). A Python Lambda streams Archive/Collection changes into OpenSearch, with schema-generated index mappings, a derived `date_range` field for date filtering, and failures sent to an SQS queue instead of being swallowed.
* `DlpAccessNext-<env>-Auth`: records which existing Cognito user pool and identity provider the environment uses. CDK never creates or changes a user pool.
* `DlpAccessNext-Web-<branch>`: Beanstalk app + environment (Node.js 24, one instance behind an HTTPS ALB), a DNS record, and the branch's own Cognito app client, with its secret in Secrets Manager. The deployed bundle is the commit at `HEAD`.

**Deploy tooling:** `npm run deploy` validates options, prints the plan, checks what is already deployed (repointed user pool, resized domain, stray tables, wrong account…) and asks before running `cdk deploy --all`. A red banner for `production`. `--yes` for CI.

**Next.js app:**
* `src/lib/appsync.ts`: server-side SigV4-signed AppSync client.
* `src/lib/auth.ts`, `/auth/login`, `/auth/logout`, `/authorize`: Cognito OIDC sign-in (ID token in an httpOnly cookie).
* `/examples/appsync-queries`: admin-only demo page that runs every query in the schema, plus a search panel.
* New deps: `@aws-sdk/credential-provider-node`, `aws4fetch`, `jose`, `openid-client`.

**Tests:** Jest assertions on every environment's synthesized templates, resolvers and deploy script; pytest for the streaming and index-template Lambdas.

**Docs:** rewritten `README.md`, new `docs/deployment.md`, PR template.



## 🧪 How Should PR Be Tested? [REQUIRED]
Prerequisites: AWS credentials for the dev account; the existing VT Cognito user pool ID (pool must have the `VT-SSO-OIDC` provider and an `admin` group); your VT account in the `admin` group. Deploys need a terminal (they prompt for confirmation).

**1. Offline checks (no AWS needed)**
```bash
npm install && npm run lint && npx tsc --noEmit && npm run build
cd infra && npm install && npm test
python3 -m venv .venv && .venv/bin/pip install -r lambda/requirements-dev.txt   # one time
npm run test:lambda
```
*Expected:* all pass.

**2. Synth without deploying**
```bash
cd infra
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
npx cdk synth --all -c backend-env=dev -c aws-account-id=$ACCOUNT -c user-pool-id=<user pool ID> -c identity-provider=VT-SSO-OIDC
```
*Expected:* three stacks (`-Data`, `-Api`, `-Auth`) synthesize with no errors.

**3. Deploy a throwaway feature backend + this branch's frontend**
```bash
npm run deploy -- -c backend-env=f-prtest -c aws-account-id=$ACCOUNT \
  -c frontend-branch=$(git branch --show-current) -c backend=provision \
  -c user-pool-id=<user pool ID> -c identity-provider=VT-SSO-OIDC
```
*Expected:* the plan lists four stacks, all `create`, and no warnings. Answering `n` exits without deploying. Answering `y` deploys (OpenSearch takes ~15–20 min). The Web stack's `AppUrl` output is `https://whunter-feature-add-deployment.dlp-access-dev.dlp.cloud.lib.vt.edu`.

**4. Exercise the app**
* Open `<AppUrl>`. `http://` redirects to `https://`.
* Open `<AppUrl>/examples/appsync-queries`. You're sent straight to VT SSO (no Cognito chooser), then back to the page.
* *Expected:* the tables are empty, so `list*` queries succeed with no items and the dependent `get*`/search queries show as **skipped**, not failed. A user not in `admin` is refused.
* Optional: put an Archive item in `Archive-dlpnext-f-prtest` (DynamoDB console). Within a minute it appears in the `list*` results and in a search from the search panel.
* `/auth/logout` signs you out.

**5. Check the safety rails (answer `n` to each)**
* Rerun step 3's command: every stack shows as `update`, no warnings.
* Rerun it without `-c identity-provider=VT-SSO-OIDC`: red warning that sign-in changes provider, prompt says "Deploy anyway?".
* `npm run deploy -- -c backend-env=production -c aws-account-id=$ACCOUNT -c user-pool-id=<user pool ID>`: red production banner, plus a line about the missing `-c production=true`.

**6. Clean up**
```bash
npx cdk destroy DlpAccessNext-Web-whunter-feature-add-deployment -c backend-env=f-prtest -c aws-account-id=$ACCOUNT -c frontend-branch=$(git branch --show-current)
npx cdk destroy --all -c backend-env=f-prtest -c aws-account-id=$ACCOUNT -c user-pool-id=<user pool ID>
```
*Expected:* both succeed; the `f-prtest` tables and OpenSearch domain are gone.



## ♿ Accessibility Testing [REQUIRED]
- [ ] Does this PR change anything in the front-end? This includes backend-only changes that may affect front end components (data schema changes, global configs, package version updates, etc.)

No user-facing pages change. The only new page, `/examples/appsync-queries`, is an admin-only developer demo, not part of the public site. The sign-in routes are redirects with no UI of their own.



## 📝 Additional Notes
**Usage (quick reference; full detail in `README.md` and `docs/deployment.md`).** Run from `infra/`. Always use `npm run deploy`, not `npx cdk deploy` (which skips the checks and confirmation).

| Goal | Command |
| --- | --- |
| Deploy/update a tier backend | `npm run deploy -- -c backend-env=dev -c aws-account-id=$ACCOUNT -c user-pool-id=<pool> -c identity-provider=VT-SSO-OIDC` |
| Deploy a branch's frontend on an existing backend | `npm run deploy -- -c backend-env=dev -c aws-account-id=$ACCOUNT -c frontend-branch=$(git branch --show-current)` |
| New feature backend + frontend together | add `-c backend=provision -c user-pool-id=<pool> -c identity-provider=VT-SSO-OIDC` with `-c backend-env=f-<slug>` |
| Production | `-c backend-env=production -c aws-account-id=<prod account> -c production=true …` (separate account) |
| CI | add `--yes` (only accepted when `CI=true`) |

Things to know:
* `-c identity-provider` and `-c production=true` must be passed on **every** deploy of an environment, or it falls back to `COGNITO` sign-in / small sizing. The deploy check warns about both.
* Only the committed `HEAD` is deployed to a frontend; uncommitted changes are listed and left out.
* A new or redeployed OpenSearch domain starts empty. Only rows written after the Api stack deploys are indexed; there is no reindex/backfill yet.
* No account IDs are stored in the repo; `-c aws-account-id` alone decides where stacks go.
* Local dev: `APPSYNC_API_URL=<GraphQLApiUrl output> npm run dev`, with the Cognito variables in `.env.local` (see `README.md`).

**Impact on existing functionality:**
* The existing PR-preview workflow (`.github/workflows/pr-preview-deploy.yaml`) still builds, but its environments now need `APPSYNC_API_URL` and the `dlp-access-next-<env>-eb` instance profile to reach the API. We should either retire it in favor of Web stacks or update it in a follow-up.
* Web stacks run `next start` (Beanstalk's `npm start`), which logs a harmless warning about `output: "standalone"`; standalone output is kept for the `Dockerfile`.
* The Amplify app and its data are untouched; nothing here reads or writes them.

**Branch for testing:** `whunter/feature/add/deployment`.



## 👥 Interested Parties

Tag any reviewers or stakeholders you'd like to include in the discussion:
@username

---

🚨[REQUIRED] -  Required fields/information in the pull request
