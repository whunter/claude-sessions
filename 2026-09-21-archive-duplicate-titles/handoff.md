# Hand-off: Archive duplicate titles + collection backfill

Tables (us-east-1, acct 226388486048):
- dev: `Archive-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev`, `Collection-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev`
- prd: `Archive-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd`, `Collection-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd`

## State
- Duplicate-title reports exist for both environments in `~/Desktop` (`duplicate_titles_{dev,prd}.{md,json}`), regenerated after the backfill and after the user's cleanup. dev: 718 titles / 3,622 records. prd: 727 titles / 3,642 records.
- Backfill done on dev and prd: 78 Archive records each had no `collection`, so it was set from the single-valued `parent_collection`. Writes were conditional (`attribute_not_exists(collection)`), 0 failures.
- 2 records per environment (`testss005003`, `testss005004`) have neither field; logged in `scripts/skipped_*_no_parent.log` and left alone.
- Nothing pending.

## Rollback
Pre-update copies of the 78 records per environment were saved as `backup_{dev,prd}_collection_fix.json` in the session scratchpad
(`/private/tmp/claude-502/-Users-whunter-dev-dlp-ingest-vtdlp-aws-tools-go/22852d57-da35-4fdd-9da6-c99fe7d1cbc1/scratchpad/`). They are not committed (record data) and the scratchpad is temporary, so copy them if you want to keep them. To undo, REMOVE `collection` from those ids.

## Scripts (`scripts/`)
- `dry.py <env> <suffix>`: read-only scan for Archive records lacking `collection`; writes `dry_<env>.json`.
- `apply_prd.py`: backup + conditional `update-item` (hard-coded to the prd table; the same script with the dev table name was used for dev).
- `enrich.py` (markdown) and `to_json.py` (JSON): build the duplicate-title reports, resolving collection and parent collection via the Collection table.

## Gotchas
- Archive `collection` is a Collection **UUID**; identifiers/titles come from the Collection table. `parent_collection` is a list (`L` of `S`) on both tables.
- Before cleanup, ~620 dev/prd records pointed at collection IDs missing from the Collection table (`eab14157-…`, `ec5add06-…`, plus a few others). The user later cleaned these up.
- dev record counts dropped between scans (11,961 → ~10,259) due to the user's cleanup, so re-run dry runs before any further write instead of trusting old counts.
- 82 records had an item-level `parent_collection` different from `collection`; the reports use the parent of the collection, not the item's own field.
- Writes to prd were initially blocked by the auto-mode classifier until the user explicitly approved.
