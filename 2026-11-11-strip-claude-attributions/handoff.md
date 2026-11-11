# Hand-off: strip Claude attributions (dlp-access-next-cdk)

## State

- `whunter/feature/add/deployment` was rewritten and force-pushed. Local and
  `origin` match, with head `15afa6b`.
- There are no attribution trailers left in `main..HEAD`.
- The backup refs were deleted, so the old history is recoverable only
  through the reflog until it expires.

## Follow-ups

- Anyone else with a checkout of this branch must reset to the new history:
  `git fetch && git reset --hard origin/whunter/feature/add/deployment`
  (or rebase their local work onto it).
- Any open PR from this branch now shows the rewritten commits. Old commit
  links in PR comments will point to commits that are no longer on the branch.
- Future commits must not include attribution trailers (see the global CLAUDE.md).

## Quick check

    git log main..HEAD --format=%B | grep -ic 'co-authored-by: claude'   # expect 0
