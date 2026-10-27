# Hand-off: human-facing tickets for dlp-access-next

**Repo:** `dlp-access-next`, branch `tickets`
**State:** 38 commits ahead of `main`. All are committed locally; the branch is **not pushed**. The last commit is `94485ab`.

## Where things are

- `docs/wayfinder/claude-tickets/` holds the original machine-written tickets 01–11. They are archived and never edited.
- `docs/wayfinder/tickets/` holds 66 human-facing tickets: parents 01–13 and their vertical-slice sub-tickets. Each has these sections: Why / What to do / Done when / Status / Blocked by / Related / Decisions / Open questions.
- `docs/wayfinder/map.md` indexes everything: the ticket tree, owner decisions, CDK requests, ADRs, research, and deferred questions. Start here.
- `docs/wayfinder/cdk-requests.md` lists CDK work C1–C10, all owned by Lee Hunter. It also has a "Not requested" section.
- `docs/adr/0002-serve-items-at-either-path.md` (Proposed) supersedes ADR 0001.

## Next steps

1. Push `tickets` and open a PR into `main` when ready.
2. Fill in the items the owner deferred (each is tracked in its ticket's Open questions and listed in map.md):
   - ADR 0002 compliance rationale, and whether ADR 0002 should move from Proposed to Accepted
   - SITE_ID env var name
   - error page wording
   - screenshot tooling and comparison deployment for the parity tests (08)
   - test data and example Items / media links (the owner will add these)
   - ARK permalink target
   - archived-flag cache invalidation (low priority)
   - header design (the dev team designer will decide)
   - Home redesign: which branch or design to follow (13b)
   - whether to build the extra `/browse/*`, `/about/*` and `/maps` pages that exist on the feature branches (13)
   - whether legacy URLs should redirect to the new `/browse/*` and `/about/*` URLs
3. Work through cdk-requests.md C1–C10 in the CDK repo.

## Notes

- Research docs under `docs/research/` still link to `claude-tickets` as their source. This is intentional background.
