# PR 21 fixes: Initial Next.js Routing & Layout

Fix instructions for the ten findings from the `/code-review` run on 2026-10-12.

- **PR:** https://github.com/vt-digital-libraries-platform/dlp-access-next/pull/21
- **Branch:** `layout-and-routing_kellyme` (base `main`), reviewed at `30519bb`
- **Repo:** `~/dev/dlp/access/dlp-access-next`

Line numbers refer to `30519bb`. Finding 1 is confirmed by `npx tsc --noEmit`. The other nine come from reading the code and were not reproduced in a browser. None of the code below has been applied or run; treat it as a starting point and test it.

## Suggested order

| Order | Finding | Why |
|---|---|---|
| 1 | 1. Browse page type errors | Blocks `next build` |
| 2 | 2. Search 404 | Broken on every page |
| 3 | 3. Dropdown closes on click | Affects every mouse and keyboard user of the desktop nav |
| 4 | 4. Dark mode, 5. Footer link name | Readability and accessibility |
| 5 | 7. Header selector, 8. Fonts | Cheap now, costly once more pages exist |
| 6 | 6. Dropdown fallback, 9. Mobile nav state, 10. Leftovers | Lower impact or optional |

## 1. Browse page fails type checking

**File:** `src/app/browse/[[...slug]]/page.tsx:12-38`

`tsc` reports two errors:

```
src/app/browse/[[...slug]]/page.tsx(32,39): error TS2345: Argument of type 'string | undefined' is not assignable to parameter of type 'string'.
src/app/browse/[[...slug]]/page.tsx(38,20): error TS7053: Element implicitly has an 'any' type because expression of type 'string' can't be used to index type '{ all: string; ... }'.
```

An optional catch-all segment (`[[...slug]]`) gives `string[] | undefined`, not `string`. At runtime Next.js passes an array (or `undefined` for `/browse`), so `slug?.at(0)` and `slug[0]` do return the first segment; only the declared type is wrong.

Replace the `Props` interface and the `browseType` calculation:

```tsx
type BrowseType = keyof typeof BrowseTypes;

interface Props {
  params: Promise<{ slug?: string[] }>
};

function isBrowseType(value: string | undefined): value is BrowseType {
  return value !== undefined && Object.keys(BrowseTypes).includes(value);
}
```

```tsx
  const { slug } = await params;
  const firstSegment = slug?.[0];
  const browseType: BrowseType = isBrowseType(firstSegment) ? firstSegment : 'all';
```

`BrowseTypes[browseType]` on line 38 then type-checks with no further change.

Use `Object.keys(...).includes` and not `value in BrowseTypes`: `in` also matches inherited keys, so `/browse/toString` would count as a valid browse type.

**Check:** `npx tsc --noEmit` reports no errors. `/browse`, `/browse/collections`, `/browse/cats`, `/browse/formats/cats` render "Everything", "Collections", "Everything", "Formats".

## 2. Header search goes to a 404

**Files:** `src/app/_components/search/SearchBar.tsx:7`, `src/app/_components/search/SearchResults.tsx`

The form submits to `/search`, and no `src/app/search/page.tsx` exists.

Add the route, following the naming used by the other pages:

```tsx
// src/app/search/page.tsx
import SearchResults from "@/app/_components/search/SearchResults";

interface Props {
  searchParams: Promise<{ q?: string | string[] }>
};

/**
 * Search results page for the site search form, which submits its query as `?q=`.
 *
 * @returns SearchPage which changes based on the `q` search parameter
 */
export default async function SearchPage({ searchParams }: Props) {
  const { q } = await searchParams;
  const query = (Array.isArray(q) ? q[0] : q) ?? "";

  return (
    <>
      <h1>Search</h1>
      <SearchResults query={ query } />
    </>
  );
}
```

Then make `SearchResults` take the query as a prop. That removes the unused `useSearchParams` import and the `'use client'` directive, which the stub doesn't need:

```tsx
interface Props {
  query: string;
}

export default function SearchResults({ query }: Props) {
  return (
    <>
      <p>[Search Results for "{ query }"]</p>
    </>
  );
}
```

If `SearchResults` later needs `useSearchParams` on the client (for pagination, say), wrap it in `<Suspense>` in the page; Next.js requires that for a statically rendered route.

**Check:** submitting the header search from any page lands on `/search?q=...` and shows the query. `npm run lint` no longer warns about the unused import.

## 3. Click or Enter closes the dropdown that hover or focus just opened

**File:** `src/app/_components/header/Header.tsx:235` and `:249`

`useHoverToOpenDropdowns` opens the popover on `pointerenter` and on keyboard focus. The trigger is still a native `popoverTarget` button, whose default action is `toggle`, so the click or Enter that follows hides the menu.

Set the action to `show` on both triggers:

```tsx
<button type="button" popoverTarget="browse-menu" popoverTargetAction="show">
```

```tsx
<button type="button" popoverTarget="about-menu" popoverTargetAction="show">
```

Closing still works through the existing paths: `popover="auto"` light dismiss (click outside, Esc), `closeWhenInactive` on pointer leave and focus out, and `closeOnLinkClick`.

The trade-off is that a touch user can no longer close the menu by tapping the trigger a second time; they tap outside it. If a second tap should close it, keep the default action and handle the click in the hook instead: call `event.preventDefault()` on the trigger's `click` and toggle only when the open was not caused by the hover or focus that preceded it.

**Check:** with a mouse, hover "Browse" then click it: the menu stays open. With a keyboard, Tab to "Browse" then press Enter: the menu stays open. Esc and clicking elsewhere close it. On a touch device or emulator, tap opens and tap outside closes.

## 4. Dark mode is half applied and search text is unreadable

**Files:** `src/app/_styles/globals.css:1-11`, `src/app/_components/search/SearchBar.css:21-29`, `src/app/_components/header/Header.css:15`

`color-scheme: light dark` tells the browser to render form controls dark on a dark OS. The search input keeps `color: var(--vt-hokieStone-8s)` with no background, so text is near-black on dark grey. The header and dropdowns hard-code `var(--vt-white)`, so they stay light while the body goes dark.

This needs a decision from the PR author: ship without dark mode for now, or support it properly.

**Option A (recommended for this PR): light only.** Nothing else in the branch is designed for dark mode, and the maroon `--primaryColor` on a dark surface would need contrast work.

In `globals.css`, delete the `@media (prefers-color-scheme: dark)` block (lines 1-6) and change:

```css
html {
  scrollbar-gutter: stable;
  color-scheme: light;
}
```

In `SearchBar.css`, give the input an explicit background so it never depends on the browser default:

```css
    input {
      /* ...existing declarations... */
      color: var(--vt-hokieStone-8s);
      background-color: var(--vt-white);
    }
```

**Option B: support dark mode.** Replace the hard-coded surface and text colours in `Header.css` and `SearchBar.css` (`--vt-white`, `--vt-hokieStone-8s`, `--vt-smoke-7t`) with the role tokens `--backgroundColor` and `--textColor`, add dark values for link hover and border colours, and check contrast for every pair. This is a design task, not a quick patch.

**Check:** set the OS to dark mode (or emulate `prefers-color-scheme: dark` in DevTools), type in the header search, and confirm the text is readable and the header and body agree.

## 5. Desktop footer logo link has no accessible name

**File:** `src/app/_components/footer/vtlib-footer/VTLibFooter.tsx:13`

At 768px and wider, `.vtlib-footer__logo` is `display: none` and the only logo link is the SVG `<a>` inside the swoop. Its only label is a `title` attribute, which is not a naming source for SVG elements.

Add `aria-label`:

```tsx
<a href="https://lib.vt.edu" title="University Libraries" aria-label="University Libraries">
```

The parent `<svg>` has `role="presentation"` while containing a focusable link. Confirm in the browser's accessibility tree that the link is still exposed; if it is not, remove `role="presentation"` from the `<svg>` and add `aria-hidden="true"` to the three decorative swoop `<path>` elements instead.

The `vtlib-footer` naming suggests this is a shared University Libraries footer copied into the repo. If so, report the fix to whoever maintains the original so it isn't lost on the next copy.

**Check:** at desktop width, the accessibility tree (or a screen reader) announces "University Libraries, link". Keyboard focus reaches it and shows a focus ring.

## 6. Dropdown positioning fallback doesn't work

**File:** `src/app/_components/header/Header.css:92-96`

Two problems in the `@supports not (...)` block:

- It uses `anchor()`, which most browsers lacking `position-area` also lack. There the `top` and `right` declarations are dropped and the menu renders unpositioned.
- Where `anchor()` does resolve, `top: calc(anchor(bottom) + 0.5rem)` leaves a gap between trigger and panel. The pointer crosses the gap, neither element is hovered on the next frame, and `closeWhenInactive` (`Header.tsx:97`) closes the menu.

First, remove the gap so the fallback matches the main path, which has none:

```css
        @supports not ((position-area: block-end span-inline-start) and (position-try-fallbacks: flip-inline)) {
          top: anchor(bottom);
          right: clamp(0.5rem, anchor(right), calc(100vw - var(--dropdown-max-width) - 0.5rem));
        }
```

Second, position the panel from script when anchor positioning is missing altogether. Popovers render in the top layer, so `position: absolute` relative to the `<li>` is not an option. Inside the `forEach` in `useHoverToOpenDropdowns`, add:

```ts
      // Fallback for browsers without CSS anchor positioning
      const positionWithoutAnchors = (event: Event) => {
        if (CSS.supports("top", "anchor(bottom)")) return;
        if ((event as ToggleEvent).newState !== "open") return;
        const rect = trigger.getBoundingClientRect();
        panel.style.top = `${rect.bottom}px`;
        panel.style.right = `${document.documentElement.clientWidth - rect.right}px`;
      };

      panel.addEventListener("beforetoggle", positionWithoutAnchors);
```

and remove the listener in the matching cleanup. `beforetoggle` covers both the native click and the script-opened paths. The panel is `position: fixed`, so viewport coordinates are correct; it will not follow the trigger if the page scrolls while open, which is acceptable for a fallback.

If supporting browsers without anchor positioning is not a goal, the alternative is to delete the `@supports not` block and say so in the PR.

**Check:** in a browser without anchor positioning (or with the feature disabled), the menu opens directly under its trigger, right-aligned, and stays open while the pointer moves from trigger to panel.

## 7. Site-header styles are attached to every `<header>`

**Files:** `src/app/_components/header/Header.css:3`, `src/app/_components/header/Header.tsx:198`

The rules hang off the bare `header` selector, with nested `button` rules. Any later `<header>` inside `<main>` (an item or article header) would inherit the grid, border, white background, padding, and button styling.

Add a class and scope to it:

```tsx
<header ref={headerRef} className="site-header">
```

```css
@layer components {

  .site-header {
```

Only the opening selector on line 3 changes; everything nested under it stays as is.

**Check:** the header looks the same at desktop and mobile widths. Temporarily add `<header><button>x</button></header>` to a page and confirm it picks up none of the site-header styles.

## 8. Heading font never loads; body font loads from the footer stylesheet

**Files:** `src/app/_styles/vars.css:79-83`, `src/app/_components/footer/vtlib-footer/VTLibFooter.css:5-31`, `src/app/layout.tsx`

**Body font (Acherus).** The two `@font-face` blocks live in `VTLibFooter.css`, under a TODO that already says to move them. Create `src/app/_styles/fonts.css`, move both blocks into it unchanged, and import it first in `layout.tsx`:

```tsx
import "@/app/_styles/fonts.css";
import "@/app/_styles/vars.css";
import "@/app/_styles/globals.css";
```

Delete the blocks and the TODO from `VTLibFooter.css`.

**Heading font (gineso-condensed).** Nothing loads it, so the site logo and mobile nav headings fall back to generic sans-serif. Gineso Condensed is served through Adobe Fonts, which needs a kit URL tied to a VT account. Get the kit URL from whoever manages VT's Adobe Fonts kits (the existing DLP access site may already use one), then add it to the root layout:

```tsx
    <html lang="en">
      <head>
        <link rel="stylesheet" href="https://use.typekit.net/KIT_ID.css" />
      </head>
      <body>
```

`KIT_ID` is a placeholder; no kit ID is recorded in this repo. Until one is available, either leave the variable as is and accept the fallback, or point `--heading_font-family` at `var(--body_font-family)` so headings at least use a loaded font.

**Check:** in DevTools, the Network tab shows the Acherus files requested on a page with the footer removed, and the Computed pane shows "gineso-condensed" as the rendered font for `.site-logo > span:first-child`.

## 9. Mobile nav state is managed by mutating the DOM (optional)

**File:** `src/app/_components/header/Header.tsx:138-187`, `:204-209`

`useMobileNavToggle` finds elements by class name and sets `hidden` and `aria-expanded` directly, so the JSX literals no longer describe the real state and a class rename breaks it silently. This works today; the change is for maintainability and can be a follow-up.

Replace the hook with component state. In `Header`:

```tsx
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLElement>(null);

  // Focus is left where the pointer put it (unlike esc key)
  useEffect(() => {
    if (!mobileNavOpen) return;

    const handleOutsidePointerDown = (event: PointerEvent) => {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (menuRef.current?.contains(target) || toggleRef.current?.contains(target)) return;
      setMobileNavOpen(false);
    };

    document.addEventListener("pointerdown", handleOutsidePointerDown);
    return () => document.removeEventListener("pointerdown", handleOutsidePointerDown);
  }, [mobileNavOpen]);

  const closeOnEscape = (event: React.KeyboardEvent) => {
    if (event.key === "Escape" && mobileNavOpen) {
      setMobileNavOpen(false);
      toggleRef.current?.focus();
    }
  };

  // Client-side navigation leaves the menu expanded otherwise
  const closeOnLinkClick = (event: React.MouseEvent) => {
    if (event.target instanceof Element && event.target.closest("a")) setMobileNavOpen(false);
  };
```

```tsx
      <button
        ref={toggleRef}
        type="button"
        className="mobile-nav-toggle"
        aria-controls="mobile-nav-menu"
        aria-expanded={mobileNavOpen}
        onClick={() => setMobileNavOpen((open) => !open)}
        onKeyDown={closeOnEscape}
      >
```

```tsx
      <nav
        ref={menuRef}
        id="mobile-nav-menu"
        aria-label="Site"
        className="mobile-nav-menu"
        hidden={!mobileNavOpen}
        onKeyDown={closeOnEscape}
        onClick={closeOnLinkClick}
      >
```

Add `useState` to the React import and delete `useMobileNavToggle` and its call. The server still renders the menu `hidden` with `aria-expanded="false"`, so the `@media (scripting: none)` fallback in `Header.css` and the no-flash behaviour are unchanged.

**Check:** at mobile width, the toggle opens and closes the menu, Esc closes it and returns focus to the toggle, tapping outside closes it, and following a link closes it. Reload with the menu closed and confirm there is no flash of the open menu.

## 10. Leftover Tailwind and scaffold files

**Files:** `postcss.config.mjs`, `package.json`, `public/`, `src/app/layout.tsx:9`, two empty CSS files

The branch removed the only `@import "tailwindcss"` and all utility classes, but the PostCSS plugin still runs on every build.

1. Remove Tailwind:

   ```bash
   npm uninstall tailwindcss @tailwindcss/postcss
   git rm postcss.config.mjs
   ```

   The Tailwind plugin was the only PostCSS plugin, and it may have been transforming the native CSS nesting and `@layer` rules on the way through. After removing it, run `npm run build` and compare the header, dropdowns, and footer in the browser before and after.

2. Delete the scaffold images. The review named `next.svg` and `vercel.svg`; a search of `src`, `README.md`, `next.config.ts`, and `Dockerfile` finds no reference to any of the five:

   ```bash
   git rm public/next.svg public/vercel.svg public/file.svg public/globe.svg public/window.svg
   ```

3. Delete the two empty stylesheets, unless they are placeholders the author intends to fill in this PR:

   ```bash
   git rm src/app/_components/items/ItemArchivePage.css "src/app/browse/[[...slug]]/page.css"
   ```

   `page.css` is imported on line 1 of `src/app/browse/[[...slug]]/page.tsx`; remove that import too. `ItemArchivePage.css` is not imported anywhere.

4. Replace the scaffold metadata description in `src/app/layout.tsx:9` (`"Generated by create next app"`) with a real one. The wording is the team's call; for example, `"Digital collections from Virginia Tech University Libraries"`.

**Check:** `npm run build` succeeds and the pages look the same as before.

## Final verification

Run from the repo root after the fixes:

```bash
npx tsc --noEmit
npm run lint
npm run build
npm run dev
```

Then walk through the manual checks listed under each finding at both a desktop width and below 768px.
