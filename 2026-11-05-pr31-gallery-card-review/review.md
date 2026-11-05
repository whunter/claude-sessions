# PR #31 review — pc-item-page-count (dlp-access)

- PR: https://github.com/vt-digital-libraries-platform/dlp-access/pull/31
- Branch: `pc-item-page-count` @ a19cf5a, diff `main...HEAD` (12 files, +388/-288)
- Mode: high effort, 8 angles, dedup only (not verified). Nothing posted to GitHub.

## Findings (most severe first)

```json
[
  {
    "file": "src/components/GalleryView.js",
    "line": 80,
    "summary": "`{itemPageCount && (...)}` renders a literal `0` when the page count is 0.",
    "failure_scenario": "getPageCount() returns 0 for any item without archiveOptions/page_count, and for every collection. React renders the number 0, so a stray '0' appears after the format tags on most cards in search, the collection show page, and Browse Collections. Use `itemPageCount > 0 &&`."
  },
  {
    "file": "src/pages/collections/BrowseCollections/BrowseCollections.tsx",
    "line": 138,
    "summary": "BrowseCollections was not updated: it still wraps GalleryView, which now returns an `<li>`, in `<div className=\"row justify-content-center\">` with no `card-display` class.",
    "failure_scenario": "On Browse Collections in Gallery view, `<li>` elements end up outside any list (invalid markup, bullets/AT list semantics), and all of CardDisplay.css is scoped under `.card-display.card-display--gallery`, so none of the card styles apply. Bootstrap `.card` plus the old `.gallery-item` sizing from CollectionsListPage.scss no longer match, which breaks the layout. The `label={false}` prop is also dead."
  },
  {
    "file": "src/pages/collections/CollectionsShowPage/CollectionTopContent.tsx",
    "line": 56,
    "summary": "Replacing CollectionDescription with `<div className=\"description full\">{description}</div>` renders the raw string[] and drops the cleanHTML/addNewlineInDesc processing.",
    "failure_scenario": "A collection description containing HTML (`<a href=...>`, `<i>`) shows as literal escaped tags. Multi-paragraph '\\n' text collapses into one run, multiple description entries are concatenated with no separator, the site-configured description heading (getDescriptionLabel) disappears, and a null description leaves an empty div. Better: keep CollectionDescription and remove only its truncation. The `CollectionDescription` import on line 3 is now unused."
  },
  {
    "file": "src/pages/collections/CollectionsShowPage/tests/collection-items.test.js",
    "line": 54,
    "summary": "Existing tests still assert the removed markup, so the suite will fail.",
    "failure_scenario": "collection-items.test.js queries `getByRole('group')` (the role/aria-roledescription were removed), checks for `collection-items-grid`, and expects the text '2 page(s)' with class `page-count-badge` (the new text is '2 pages'). thumbnail.test.js expects the 'Item'/'Collection' labels that were deleted from Thumbnail. Cypress specs select `.gallery-item`, `div.gallery-item > div.card > a`, and `div.row > ... div.card-body > a > h3` (browse_collections, view_options, language_config, search_bar), and none of those exist any more."
  },
  {
    "file": "src/pages/search/ItemsList.js",
    "line": 27,
    "summary": "The container is now always a `<ul>`, even for the List and Masonry views, whose children are `<div>`s. CollectionItems list view (`<ul className=\"collection-items-list\">` line 97) has the same problem.",
    "failure_scenario": "In search List/Masonry view and collection list view, a `<ul>` holds `<div>` children (invalid HTML that screen readers announce as an empty/odd list). The browser's default `ul` padding-left (40px) and margins are not reset outside `.card-display--gallery`, so the Bootstrap `.row`, `.card-columns` and `.collection-items-list` layouts shift right. Use `<ul>` only for the Gallery view, or reset list styles."
  },
  {
    "file": "src/components/GalleryView.js",
    "line": 11,
    "summary": "GalleryView's getPageCount calls JSON.parse with no try/catch. The collection grid it replaces used CollectionItems' guarded getPageCount.",
    "failure_scenario": "One item with malformed archiveOptions (e.g. a non-JSON legacy string) now throws during render and takes down the whole collection show page or search results page. Before, the collection grid returned 0. Reuse the guarded helper by moving CollectionItems.getPageCount into a shared lib and calling it from both places, which also removes the duplicate."
  },
  {
    "file": "src/components/GalleryView.js",
    "line": 23,
    "summary": "Removed behaviors: the `item_category !== 'iawa'` format suppression, the clickable format facet links (`/search?...&format=X`), and the card description.",
    "failure_scenario": "IAWA site cards now show format tags that were intentionally hidden. Users can no longer click a format on a card to filter search. The description preview is gone from every gallery card, and `cleanHTML` is now an unused import. If any of this is intentional, the iawa guard at least should be deliberately re-added or dropped."
  },
  {
    "file": "src/components/GalleryView.js",
    "line": 33,
    "summary": "The format fallback `format.split('/')[0]` shows raw lowercase MIME top-level types, and collections get a lowercase 'collection' tag.",
    "failure_scenario": "format 'application/msword' or 'application/zip' becomes the tag 'APPLICATION'. 'video/mp4', 'audio/mpeg' and 'text/plain' become generic lowercase types, unlike the curated 'Image'/'PDF'/'3D Model' labels. Screen readers announce 'Format: collection' for collections. Map the known types and fall back to the full value or 'Item'."
  },
  {
    "file": "src/css/CardDisplay.css",
    "line": 121,
    "summary": "`grid-template-rows: auto fit-content;` is invalid CSS (fit-content() requires an argument), so the browser drops the declaration.",
    "failure_scenario": "The card body's intended two-row layout never applies, and it silently falls back to implicit auto rows. Also, `padding-bottom: 8px` on `.card` is overridden by the later `padding: 0`, and `display: grid` is declared twice on `.image-container`, which is dead CSS. Use `auto fit-content(100%)` or `auto min-content`."
  },
  {
    "file": "src/components/GalleryView.js",
    "line": 61,
    "summary": "Callers still compute and pass a `category` prop, which GalleryView now ignores in favor of re-deriving getCategory(item). Thumbnail's `category` prop is also dead.",
    "failure_scenario": "ItemsList, CollectionItems and BrowseCollections all pass `category=...` (BrowseCollections passes the explicit 'collection'), but GalleryView calls getCategory twice and ignores the prop. Any collection object without `collection_category` would now link to /archive/... even though the caller said 'collection'. Also left behind: the unused `ReactNode` import in CollectionItems.tsx, the commented-out sr-only 'Pages' span, and the unused `category` prop in Thumbnail.tsx. Pick one source of truth: either use props.category or drop the prop everywhere."
  }
]
```
