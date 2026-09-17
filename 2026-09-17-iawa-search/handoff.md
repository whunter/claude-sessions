# Hand-off: iawa-search — duplicate federated/iawa Archive record cleanup

**Directory:** `~/Desktop/iawa-search` (outputs, not in any git repo)

## Current state

- Deleted 1,984 duplicate records from `Archive-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev` (dev, account `226388486048`) and 718 from `Archive-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd` (pre-production, same account). Both were records tagged `item_category = "federated"` whose identifier/title/description all matched a record tagged `"iawa"` in the separate production account (`196766403141`).
- Full pre-delete backups (complete DynamoDB item JSON, one per line) exist for both deletions in `~/Desktop/iawa-search/backups/`.
- The two Collection tables in the same account had 0 federated/iawa matches, so nothing was deleted there. The two iawa-account tables were only read, never modified.

## Not yet done

- No verification pass beyond spot-checking one deleted `id` per table with `get-item`. Have not re-run the full scan to confirm all 2,702 target ids are gone (should be, since batch-write-item reported 0 unprocessed items on both runs, but wasn't independently re-verified at scale).
- Did not investigate *why* these duplicates exist (e.g. a bad past migration/sync job) — only found and removed them. If this is an ongoing sync issue, the root cause producing new "federated" duplicates of "iawa" records may still be active.
- Did not clean up `~/Desktop/iawa-search/*.csv` output files or the `backups/` directory — left in place in case they're needed for reference or further review.

## Next steps

1. If a restore is ever needed, replay the relevant backup JSONL through `batch-write-item` PutRequests (25 items per batch) against the matching table — see `~/dev/dlp/claude-sessions/2026-09-17-iawa-search/summary.md` for exact table names and backup file paths.
2. Consider checking why "federated" duplicates of iawa-owned items exist in the dlp-access account at all — worth investigating the ingest/sync pipeline that populates that `item_category` field, in case it needs a fix to prevent recurrence.
3. Confirm with the user whether the two Collection tables (0 matches this time) and any other `item_category` values (e.g. `swva`, `hokies` seen in sampling) also warrant similar duplicate audits.
4. AWS credential note: `--profile eb-cli` (not `AWS_PROFILE=eb-cli` as an env var) is required to reach account `226388486048` — default shell env credentials point to `196766403141`. Worth flagging to the user if this seems like an unintended credential rotation.
