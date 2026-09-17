# Session: iawa-search — find and remove duplicate "federated" records that are actually IAWA-owned

**Date:** 2026-09-17
**Directory:** `~/Desktop/iawa-search` (outputs), no code repo touched
**Goal:** Find DynamoDB Archive/Collection records tagged `heirarchy_path` with 3+ values, then find records tagged `item_category`/`collection_category` = "iawa" in the production account, cross-reference those against records tagged "federated" in the dlp-access dev/preprod account (same title/identifier/description = duplicate), and delete the confirmed federated duplicates.

## Accounts and tables involved

- **226388486048** (dlp-access dev/preprod, profile `eb-cli`):
  - `Archive-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev` (dev)
  - `Collection-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev` (dev)
  - `Archive-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd` (pre-production, despite the `prd` naming)
  - `Collection-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd` (pre-production)
- **196766403141** (iawa/production, default env credentials):
  - `Archive-ocrvf7v6rbdyrkx42edgadqo6u-production`
  - `Collection-ocrvf7v6rbdyrkx42edgadqo6u-production`

## Step 1: heirarchy_path >= 3 values (four 226388486048 tables)

Note: the field is genuinely spelled `heirarchy_path` in the schema — a 10-year-old typo, not something to "fix". Scanned all four tables via paginated `aws dynamodb scan` (projection on `id`, `identifier`, `heirarchy_path`), filtered for items where the `heirarchy_path` list has 3+ entries, wrote one CSV per table to `~/Desktop/iawa-search/`:

- `Archive-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev.csv` — 366/18,214
- `Archive-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd.csv` — 168/17,147
- `Collection-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev.csv` — 228/452
- `Collection-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd.csv` — 15/100

## Step 2: iawa-category records (196766403141)

Scanned both production tables (projection on `id`, `identifier`, `title`, `description`, `item_category`/`collection_category`), filtered for category == "iawa" (case-insensitive), wrote:

- `Archive-ocrvf7v6rbdyrkx42edgadqo6u-production-iawa.csv` — 3,370 of 27,468
- `Collection-ocrvf7v6rbdyrkx42edgadqo6u-production-iawa.csv` — 30 of 108

## Step 3: cross-reference "federated" records against the iawa lists

Built normalized (lowercased/trimmed) lookup sets of identifier/title/description from both iawa CSVs, then rescanned the four 226388486048 tables (adding `title`/`description` to the projection) and flagged any record with `item_category`/`collection_category` == "federated" whose identifier, title, AND description all exactly matched an iawa record. All matches found were full triple-matches (not coincidental single-field overlaps on generic text) — genuine duplicate items that exist in both the iawa production account and the dlp-access account, tagged differently.

- `Archive-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev-federated-iawa-matches.csv` — 1,984 matches
- `Archive-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd-federated-iawa-matches.csv` — 718 matches
- `Collection-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev-federated-iawa-matches.csv` — 0 matches
- `Collection-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd-federated-iawa-matches.csv` — 0 matches

## Step 4: deletion (only the two Archive tables, both confirmed by user first)

For each table: fetched full item data for every matched `id` via `batch-get-item` (chunks of 100), wrote a JSONL backup to `~/Desktop/iawa-search/backups/`, then deleted via `batch-write-item` DeleteRequests (chunks of 25). Both runs completed 100% with zero errors/unprocessed items; spot-checked one deleted `id` per table afterward with `get-item` returning empty.

- **Archive-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev** (dev): 1,984/1,984 deleted. Backup: `backups/Archive-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev-deleted-items-backup-20260917T163823Z.jsonl`
- **Archive-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd** (pre-production): 718/718 deleted. Backup: `backups/Archive-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd-deleted-items-backup-20260917T164450Z.jsonl`

The two Collection tables were **not** touched (0 matches, and also not requested). No records were deleted from the two iawa-account (196766403141) tables.

## Credential quirk discovered mid-session

Default AWS env credentials (`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` in the shell env) resolved to account `226388486048` at the very start of the session, but later in the same session resolved to `196766403141` instead — with no explicit profile switch on my part. The only saved CLI profile, `eb-cli`, correctly targets `226388486048`, but only when passed as an explicit `--profile eb-cli` flag — setting `AWS_PROFILE=eb-cli` as an env var did *not* override the (higher-precedence) env-var credentials and still resolved to `196766403141`. Used `--profile eb-cli` for all `226388486048` operations from that point on.

## State at end of session

- All CSVs and backups are local files under `~/Desktop/iawa-search/`, not committed anywhere.
- No code changes were made in this repo (`dlp-access`); this was purely an ad hoc AWS data investigation/cleanup task.
