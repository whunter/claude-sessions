# Hand-off: Archive page "Language" field links to Wikipedia instead of search facet

**Repo:** `dlp-access` (branch `prod`)

## Current state

- `src/components/CollapsibleCards.js` modified, not committed.
- Fix: added `"language"` to the `facetSearchItems` array and removed the hardcoded `key === "language"` branch that linked every item to the Wikipedia "English language" article regardless of its actual value (bug introduced in commit `d9b4b202`).
- Language now generates `/search?q=&field=all&view=Gallery&language=<value>` the same way `format`/`type`/`tags` do.

## Not yet done

- No commit made.
- No manual/browser verification against a running `dlp-access` instance — the fix was derived from tracing the render logic, not confirmed by clicking through the UI.

## Next steps

1. Run `dlp-access` locally (or on a preview env) and click the Language field on an archive page (e.g. `/archive/954020a8`) to confirm it now lands on `/search` with the language facet applied, for items with non-English languages too.
2. Commit `src/components/CollapsibleCards.js` on branch `prod` (or a feature branch off it, depending on this repo's workflow) with a message referencing the bug.
3. Since `prod` is presumably a protected/live branch, confirm the right process (PR vs. direct commit) before pushing.
