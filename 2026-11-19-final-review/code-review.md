# Code review: `whunter/feature/add/deployment` vs upstream `dlp-access-next`

- **Date:** 2026-11-19
- **Repo:** `dlp-access-next-cdk`, branch `whunter/feature/add/deployment` (HEAD `e312bb4`)
- **Fixed point:** `vt-digital-libraries-platform/dlp-access-next` `main` = `b307722`, which is also the merge-base
- **Diff:** `git diff b307722...HEAD`. That is 163 commits and 78 files, +18,631 / −848, mostly lockfiles.
- **Method:** a two-axis review, with Standards and Spec run by separate parallel sub-agents. The findings are not merged or re-ranked across the two axes.

**Sources used**
- **Standards:** the repo has no `CODING_STANDARDS.md` or `CONTRIBUTING.md`. The reviewer used `eslint.config.mjs`, both `tsconfig.json` files, `.gitattributes`, the PR template, `README.md`, `docs/deployment.md` and the author's global no-AI-credit rule. It also used the Fowler smell baseline.
- **Spec:** there are no issue references in the commits. The primary spec is `docs/infra/eb-frontend-spec.md`. Secondary sources are `docs/deployment.md`, `docs/opensearch-streaming.md` and `README.md`, plus the multi-env decisions from the 2026-09-24 grilling notes.

---

## Standards

**Documented standards: no hard violations.**
- **No-AI-credit rule:** no hits in `infra/`, `src/`, `docs/` or `README.md`.
- **`.gitattributes`:** `.ebextensions` and `.platform` files are LF. The `export-ignore` list matches `docs/infra/eb-frontend-spec.md:86`.
- **`eslint.config.mjs`:** the `infra/cdk.out/**` ignore follows the file's existing comment style. Root `tsconfig.json` excludes `infra`, which `infra/tsconfig.json` covers. That's consistent.
- **README, `docs/deployment.md`, PR template:** none of them define coding conventions.
- **Loose end:** `prettier` 3.9.10 was added to the root `package.json` with no config and no script, so nothing runs it.

**Baseline smells** (all judgement calls)

1. **Duplicated Code: deploy confirmation flow.** `infra/bin/deploy.ts:75-87` writes the `--yes`/prompt logic out inline. `infra/lib/frontend/frontend-cli.ts:226-236` already has it as `confirm(io, yes, question)`. Moving the backend `main()` into `lib/deployment/deploy-cli.ts` behind an IO seam would match `frontendDeploy` and make it testable the same way.
2. **Duplicated Code: Cognito client listing.** `infra/lib/frontend/deploy.ts:261-283` (`findClient`) and `infra/lib/frontend/destroy.ts:155-170` (`deleteClients`) repeat the `list-user-pool-clients` call and the filter by `ClientName`. The pagination comment is copied too. This could be one `listClients(...)` in `lookups.ts`.
3. **Duplicated Code / Data Clumps: session cookie options.** `src/app/auth/login/route.ts:33-42` and `src/app/authorize/route.ts:50-56` both build `{ httpOnly, sameSite: "lax", secure, path: "/" }`, and logout repeats the clear-cookie shape. A `cookieOptions(request)` helper in `src/lib/auth.ts` would keep the security attributes in one place.
4. **Data Clumps: CLI option set.** `frontend-cli.ts:204-210` types `planWithRunner(values: {...})` inline. The same option set is declared again in the deploy and destroy `parseArgs` maps. One shared options constant and type would remove the copy.
5. **Primitive Obsession (minor): `CI` flag.** `CI` is passed as `string | undefined` through `deployArgs`, `frontendDeploy` and `frontendDestroy`, and each one runs `checkYesInCi`. Normalising it to a boolean once at the entry point would simplify all three.
6. **Possible Duplicated Code: second GraphQL client.** `src/lib/appsync.ts` (IAM-signed) sits next to the existing `src/app/_utils/fetchUtils/graphqlRequest.ts` (API key). The auth differs, so this may be intended. Document which one new code should use.

There was no Speculative Generality, Middle Man or Refused Bequest worth flagging. `frontend/deploy.ts` is 561 lines, but each function is one step of the deploy.

---

## Spec

`docs/infra/eb-frontend-spec.md` is mostly implemented and well tested. The Web stack has been removed and the old options are rejected. The Api stack has the service role, its SSM parameter and the `dlpnext/*` grant. Plan, deploy, destroy and status all run through an injected `CommandRunner`.

**(a) Missing or partial**

- **Story 5:** the spec says "deploy a branch other than the one checked out with a flag, so that I can redeploy or rebuild someone else's frontend". `frontend-cli.ts:55-57,255-263` refuses `--branch` unless it matches the checked-out branch or HEAD is detached. The guard is sound, since HEAD is what gets bundled, but the story as written isn't met. Update the spec or the docs.
- **Story 47:** the spec says "`CI=true` or `--yes` to skip the confirmation prompt". In practice `CI=true` alone still prompts, and `--yes` outside CI is refused (`frontend-cli.ts:191-196`, `deploy-cli.ts:91`), so both are required. This matches the existing backend deploy, so the story's "or" is what's wrong.
- **Testing decision:** the spec says "later deploy: only `eb deploy` with the `<slug>-<sha>` label". A redeploy also upserts the CNAME and re-runs `eb init` (`deploy.ts:131-138`). Both are harmless and deliberate (recovery and fresh clones), but they depart from "only".

**(b) Not asked for (scope creep)**

- **AppSync queries example:** `src/app/examples/appsync-queries/**` isn't in the EB spec. It comes from earlier backend work (f05f1ff, 6334bc7).
- **Cognito auth routes:** `src/app/auth/{login,logout}`, `src/app/authorize` and `src/lib/auth.ts`. The spec assumes these exist ("callback URLs `<origin>/authorize`", `COGNITO_*`), so they count as a prerequisite and are acceptable.
- **PR template:** `.github/PULL_REQUEST_TEMPLATE.md` (23751a0) isn't related to any spec.
- **Lifecycle policy role switching:** `frontend.ts:159-219` also moves the policy to a new role when the old role's backend is gone. It's reasonable, but beyond what the spec asks.
- **Destroy guard:** destroy refuses when the backend tag doesn't match (`destroy.ts:58-70`). The spec doesn't ask for this, but it protects the other backend's client.

**(c) Implemented, but differs from the 2026-09-24 settled decisions**

> **Reviewer note (aggregator):** these are measured against the September grilling notes. Later commits deliberately revised several of them, for example 72f078d "Add -c production flag for production sizing", and the current code comments document the newer behaviour. Treat them as "confirm the spec and notes are updated", not as bugs.

- **Production search sizing:** the notes say "prod 2x m7g.medium 2-AZ 1 replica". `environments.ts:52-61` sets 3 nodes across 3 AZs, and the README and `docs/deployment.md` agree with the code. Sizing follows `-c production=true`, not the env name, so `production` without the flag gets one `t3.small.search` node. `cec5d2c` warns about shrinking production at confirm time, which softens this, but the env name still doesn't imply the sizing.
- **Production account placeholder:** the notes say "throws at synth". Nothing throws: the account comes from `-c aws-account-id` (`app.ts:110-118`).
- **RETAIN scope:** RETAIN, deletion protection and PITR apply only to the tables. The OpenSearch domain is always `DESTROY` (`data-stack.ts:103`), which is documented in `environments.ts:27-28` and recoverable through resync. Confirm this is intended.
- **Feature env naming:** the notes say `<feature>`, but the code requires the `f-` prefix (`environments.ts:87`).

**Checked and matching:** the streaming Lambda (python3.12, 3 retries, 30s timeout, Archive and Collection only, `api-stack.ts:324-340`), the `.gitattributes` bundle excludes, the removal of `.ebignore`, and the static `.ebextensions` settings that the tooling never sets (`frontend.test.ts:1009`).

---

## Summary

**Standards:** no documented-standard violations. There are 6 judgement-call smells; the worst is the confirmation and Cognito-listing logic duplicated between the backend and frontend CLIs.

**Spec:** 3 partial requirements, 5 unrequested behaviours and 4 departures from the September notes. The worst is that Story 5 (`--branch` for someone else's frontend) contradicts the implemented guard, so the spec needs updating to match the code.
