# Code review: `fetch-utils_padma012` vs `main`

- **Repo:** `dlp-access-next`
- **Date:** 2026-10-14
- **Scope:** `git diff main...HEAD` (30 commits, 37 files, +2569/-105). Only this branch was reviewed.
- **Method:** High-effort recall review. Eight angles: line-by-line, removed behavior, cross-file, reuse, simplification, efficiency, altitude, and conventions. Findings were deduped but not verified.
- **Checks run:** `npx tsc --noEmit` reports 2 errors, both in `src/app/browse/[[...slug]]/page.tsx`.
- **CLAUDE.md:** the repo has none. No commit on the branch breaks the global no-attribution rule.

## Findings (most severe first)

### 1. The browse page fails type-checking, so `next build` breaks
`src/app/browse/[[...slug]]/page.tsx:12, 32, 38`

`params` is typed as `{ slug: string }`, but `[[...slug]]` gives `string[] | undefined`. Because of this:
- `includes(slug?.at(0))` has a `string | undefined` argument (TS2345).
- `BrowseTypes[browseType]` indexes the object with an unrestricted `string` (TS7053).

Under `strict: true`, Next 16 runs this type-check during `next build`, so the build fails.

**Fix:** type `params` as `Promise<{ slug?: string[] }>`, declare `BrowseTypes` `as const`, and narrow with a `keyof typeof BrowseTypes` type guard.

### 2. Collection Organization links can produce multi-segment URLs
`src/app/_components/collection/CollectionOrganization.tsx:13`

The link is `href={`/collection/${node.custom_key}`}`. Item links on the collection page go through `toSlug()`, but these do not. If the map's `custom_key` holds a full ARK (`ark:/53696/abc`), the href becomes `/collection/ark:/53696/abc`. That URL has three path segments, so it does not match `[slug]` and returns a 404.

This copies dlp-access's `CollectionTreeItem` exactly, and dlp-access's test fixtures use short keys, so it may be harmless today. `toSlug` is idempotent, so wrapping the key with it is cheap insurance.

### 3. Transient API or network failures show up as 404 Not Found
`src/app/_utils/fetchUtils/getCollectionDetails.ts:446`, `getItemDetails.ts:721`

Both functions catch every error and return `null`. The pages then call `notFound()`. A missing or wrong `NEXT_PUBLIC_AWS_APPSYNC_*` env var, an AppSync outage, a GraphQL error, or a malformed `%` slug that makes `decodeURIComponent` throw all render "404 Not Found" instead of a 500 or error boundary. That hides misconfiguration and tells crawlers the page is gone.

**Fix:** return `null` only when the lookup finds nothing, and let real errors throw (to `error.tsx`).

### 4. The item page skips visibility and site checks on the parent collection
`src/app/_utils/fetchUtils/getItemDetails.ts:716-720`, `getCollectionDetails.ts:405-418`

`getCollectionById` fetches the parent and top-level collections with `getCollection(id)`, which has no `visibility` or `collection_category` filter. A visible item whose collection is hidden, or belongs to another site, still renders, along with that collection's data. The same applies to `topLevel` on the collection page: a visible sub-collection can expose a hidden top-level parent's thumbnail.

**Fix:** decide whether this matches dlp-access's intent. If not, check `visibility` and the category on the fetched collection.

### 5. Collection and item lookups match `custom_key` differently
`src/app/_utils/fetchUtils/getCollectionDetails.ts:437` vs `getItemDetails.ts:709`

Collections use `matchPhrase` and take `limit: 1`. Items use `eq`. On an analyzed OpenSearch field, `matchPhrase` can match more than one document when one key's tokens are a sub-phrase of another's. The query then returns whichever scores first, which could be the wrong collection. This mirrors dlp-access, but there is no exact-match check on the result.

**Fix:** after the query, check `collection.custom_key === toCustomKey(customKey)`, or use `eq` if the field is a keyword.

### 6. The site-wide search form submits to a route that doesn't exist
`src/app/_components/search/SearchBar.tsx:180`

The form uses `action="/search"`, but there is no `src/app/search/` route. Every header search lands on a 404. `SearchResults.tsx` exists, but no page uses it, and it imports `useSearchParams` without using it, which triggers a lint warning.

**Fix:** add `src/app/search/page.tsx`, even as a stub.

### 7. The collection page runs independent requests one after another
`src/app/collection/[slug]/page.tsx:46-47`

`getCollectionItems(collection.id)` and `getCollectionMap(collection, topLevel)` don't depend on each other, but each `await`s in turn. That adds a full AppSync round trip to every collection page render.

**Fix:** `const [{ items, total }, map] = await Promise.all([...])`.

### 8. Pages and fetch helpers have no caching or deduplication
`src/app/_utils/fetchUtils/graphqlRequest.ts:814`

`fetch` is a POST with no `next: { revalidate }` and no `cache` option. In Next 16 that means every request hits AppSync, with no Data Cache. No `generateMetadata` exists yet. Once one is added that calls `getCollectionDetails` or `getItemDetails`, the same lookup will run twice per request, because POST fetches aren't memoized.

**Fix:** wrap the getters in React `cache()` and pass an explicit `revalidate`.

### 9. `getCollectionMap` uses `??`, so an empty-string map ID skips the parent fallback
`src/app/_utils/fetchUtils/getCollectionMap.ts:588`

If a sub-collection has `collectionmap_id: ""`, `??` keeps the empty string, the function returns `null`, and the parent's map is never tried. Using `||` would fall back as intended.

Related: `sortTree`'s comparator never returns 0 for equal names or numbers, so the sort order is unstable when siblings share a name.

### 10. Leftover scaffolding and duplicate landmark labels
- `src/app/layout.tsx:1139`: the metadata `description` is still "Generated by create next app".
- `src/app/_components/header/Header.tsx`: both `<nav>` elements have `aria-label="Site"`, so screen readers announce two identical landmarks. Label the mobile one distinctly, e.g. "Site (mobile)".
- `src/app/_components/items/ItemArchivePage.css` and `src/app/browse/[[...slug]]/page.css` are empty files.

## Pre-noted item (not implemented yet): local-dev secrets command

The current local-dev command is:

```sh
eval "$(aws secretsmanager get-secret-value --secret-id ci/dlp-access-next/deploy-app-secrets \
  --query SecretString --output text | python3 -c '...shlex.quote...')" && npm run dev
```

It should be replaced, for three reasons:

- **Unneeded dependency:** `python3` is there only to parse a flat JSON object.
- **Injection through keys:** `eval` can be injected through the secret's keys. `shlex.quote` and `jq @sh` quote only the values, not the keys. A key like `C;echo PWNED` executed when tested with the jq equivalent.
- **Silent failure:** piping into `eval` hides an `aws` failure, so `next dev` can start without its secrets.

**Proposed fix:** add `scripts/dev.mjs` that:

1. Runs `execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", "ci/dlp-access-next/deploy-app-secrets", "--query", "SecretString", "--output", "text"])` with no shell.
2. Runs `JSON.parse` on the result.
3. Calls `spawn("next", ["dev", ...process.argv.slice(2)], { stdio: "inherit", env: { ...process.env, ...secrets } })`.
4. Exits with a non-zero code if `aws` fails.

Wire it in `package.json`:
- `"dev": "node scripts/dev.mjs"`
- `"dev:local": "next dev"`, to run without AWS.

A `predev` hook can't do this, because it runs as a separate process and can't pass env vars to `dev`.

## JSON findings

```json
[
  {"file": "src/app/browse/[[...slug]]/page.tsx", "line": 32, "summary": "params typed as { slug: string } for an optional catch-all; tsc reports TS2345/TS7053 under strict mode", "failure_scenario": "next build runs type-checking -> build fails on this file"},
  {"file": "src/app/_components/collection/CollectionOrganization.tsx", "line": 13, "summary": "Tree links use raw node.custom_key instead of toSlug()", "failure_scenario": "map custom_key 'ark:/53696/abc' -> href /collection/ark:/53696/abc -> multi-segment URL, no [slug] match, 404"},
  {"file": "src/app/_utils/fetchUtils/getCollectionDetails.ts", "line": 446, "summary": "All fetch errors swallowed to null, which pages turn into notFound()", "failure_scenario": "AppSync outage or missing env var -> every collection/item page returns 404 instead of an error"},
  {"file": "src/app/_utils/fetchUtils/getItemDetails.ts", "line": 717, "summary": "Parent and top-level collections fetched by ID without visibility/category checks", "failure_scenario": "visible item in a hidden collection -> page renders and exposes the hidden collection's data"},
  {"file": "src/app/_utils/fetchUtils/getCollectionDetails.ts", "line": 437, "summary": "custom_key matched with matchPhrase + limit 1 and no exact-match check (items use eq)", "failure_scenario": "analyzed field tokens overlap between keys -> wrong collection rendered for a slug"},
  {"file": "src/app/_components/search/SearchBar.tsx", "line": 180, "summary": "Search form posts to /search, which has no route", "failure_scenario": "any header search -> 404"},
  {"file": "src/app/collection/[slug]/page.tsx", "line": 46, "summary": "Independent getCollectionItems and getCollectionMap awaited sequentially", "failure_scenario": "extra AppSync round trip on every collection page render; use Promise.all"},
  {"file": "src/app/_utils/fetchUtils/graphqlRequest.ts", "line": 814, "summary": "POST fetch with no revalidate/cache and getters not wrapped in React cache()", "failure_scenario": "every render hits AppSync; a future generateMetadata doubles each lookup"},
  {"file": "src/app/_utils/fetchUtils/getCollectionMap.ts", "line": 588, "summary": "?? does not fall back to topLevel map when collectionmap_id is an empty string; sort comparator never returns 0", "failure_scenario": "sub-collection with collectionmap_id '' -> no Collection Organization tree shown"},
  {"file": "src/app/layout.tsx", "line": 1139, "summary": "Scaffold metadata description left in; duplicate aria-label='Site' navs in Header; empty CSS files", "failure_scenario": "'Generated by create next app' appears in search snippets; screen readers announce two identical landmarks"}
]
```
