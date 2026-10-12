# PR 21 changes: Initial Next.js Routing & Layout

- **PR:** https://github.com/vt-digital-libraries-platform/dlp-access-next/pull/21
- **Author:** Kelly Ervin Mills (`ervinkellym`)
- **Branch:** `layout-and-routing_kellyme` into `main`, read at `30519bb`
- **Size:** 28 files, 1,905 additions, 105 deletions, 29 commits
- **State on 2026-10-12:** open, mergeable, not a draft, no reviews yet. Review requested from `whunter`, `padma012`, `badmintoncat`, `goynejennifer`.

## Summary

The PR replaces the `create-next-app` starter page with the skeleton of the new access site: a root layout with a new header and the VT Libraries footer, global styles and design tokens, and placeholder pages for every public route except search.

**It should not merge as it stands: `npm run build` fails on a type error in the browse page.** Nothing in CI reports this, because the only workflow (the preview deploy) was skipped. `npm run lint` also fails, with nine errors in the accessibility page.

The rest of the adverse implications are behaviour, accessibility, and maintenance concerns. They are listed under [Adverse implications](#adverse-implications), most severe first.

## How this was checked

| Check | Result |
|---|---|
| `npm run build` | Fails: type error at `src/app/browse/[[...slug]]/page.tsx:32` |
| `npx tsc --noEmit` | 2 errors, both in the browse page (lines 32 and 38) |
| `npm run lint` | 9 errors, 2 warnings |
| `gh pr checks 21` | One check, `deploy-preview`, skipped |
| Browser testing | Not done |

Everything else in this document comes from reading the diff. Items that depend on browser behaviour are marked "not reproduced".

`pr21-fixes.md` in this directory has fix instructions for ten of the issues below. The lint failure, the missing CI signal, the catch-all 200 responses, the missing page gutter, and the browser-support point are new in this document.

## What the PR changes

### Root layout and home page

| File | Change |
|---|---|
| `src/app/layout.tsx` | Removes the Geist fonts loaded through `next/font`. Wraps every page in `<Header />`, `<main>`, `<Footer />`. Imports `vars.css` and `globals.css`. Sets the page title to "VT Digital Library Platform". |
| `src/app/page.tsx` | Replaces the starter page with an `<h1>` and one placeholder sentence. |
| `src/app/globals.css` | Deleted. It held the only `@import "tailwindcss"`. |

Every page now gets the same header, footer, and `<main>` landmark, so pages return only their own content.

### Shared styles (`src/app/_styles/`)

| File | Change |
|---|---|
| `vars.css` | Design tokens as CSS custom properties: VT brand colours, colour roles (`--primaryColor`, `--textColor`, and so on), font families, focus outlines, radii, padding, size limits, a 44px minimum touch target, and transition timings. |
| `globals.css` | Page skeleton (body is a three-row grid: header, content, footer), width limits on `<main>` at four breakpoints, a `.visually-hidden` utility, global focus rings, and a dark-mode override of the background and text colours. |

### Header (`src/app/_components/header/`)

`Header.tsx` is a client component with three parts:

- **Site name link** to `/`.
- **Desktop navigation:** "Browse" and "About" buttons, each opening a dropdown built on the native Popover API (`popover="auto"`). A hook, `useHoverToOpenDropdowns`, adds opening on mouse hover and on keyboard focus, and closing when the pointer and focus have both left. Closing on outside click and Esc comes from the browser.
- **Mobile navigation (768px and below):** a hamburger button that expands an in-page menu, pushing the content down. A second hook, `useMobileNavToggle`, handles the toggle, Esc, outside taps, and closing after a link is followed.

`Header.css` positions the dropdowns with CSS anchor positioning, animates both menus (skipped when the user prefers reduced motion), and switches to a three-row grid on mobile. With JavaScript off, the mobile menu is shown expanded and the hamburger is hidden.

The Browse menu links to `/browse`, `/browse/collections`, `/browse/formats`, `/browse/items`, `/browse/locations`, and `/browse/partners`. The About menu links to `/about`, `/accessibility`, `/feedback`, `/about/metadata`, and `/about/permissions`.

### Search (`src/app/_components/search/`)

| File | Change |
|---|---|
| `SearchBar.tsx`, `SearchBar.css` | A `<search>` landmark holding a plain GET form that submits to `/search?q=...`. It has a hidden label and a magnifying-glass submit button. It works without JavaScript. |
| `SearchResults.tsx` | A stub that renders "[Search Results]". Nothing uses it yet. |

### Icons (`src/app/_components/icons/`)

`CustomIcons.tsx` exports three inline SVG icons (chevron, hamburger, magnifying glass), all hidden from assistive technology. `CustomIcons.css` sizes them and animates the chevron when its dropdown opens and the hamburger into an "X" when the mobile menu opens.

### Footer (`src/app/_components/footer/`)

| File | Change |
|---|---|
| `Footer.tsx` | A `<footer>` wrapping `VTLibFooter`. |
| `vtlib-footer/VTLibFooter.tsx`, `.css` | The shared VT University Libraries footer, copied in as static markup and CSS (766 lines, 27 links). The PR asks reviewers not to review it. Its stylesheet also declares the `Acherus` font, loaded from `www.assets.cms.vt.edu`. |

### Routes

All pages are placeholders (an `<h1>` and one sentence) except Accessibility.

| Route | File | Behaviour |
|---|---|---|
| `/` | `page.tsx` | Home placeholder |
| `/about` | `about/page.tsx` | Placeholder |
| `/about/metadata` | `about/metadata/page.tsx` | Placeholder |
| `/about/permissions` | `about/permissions/page.tsx` | Placeholder |
| `/about/platform` | `about/platform/page.tsx` | Placeholder. Not linked from the header. |
| `/accessibility` | `accessibility/page.tsx` | Static text copied from the production site |
| `/feedback` | `feedback/page.tsx` | Placeholder |
| `/browse/...` | `browse/[[...slug]]/page.tsx` | One page for all browse views. The first path segment picks the view (`all`, `collections`, `items`, `formats`, `locations`, `partners`); anything else falls back to "Everything". |
| `/collection/[slug]` | `collection/[slug]/page.tsx` | Echoes the slug |
| `/item/[slug]`, `/archive/[slug]` | `item/[slug]/page.tsx`, `archive/[slug]/page.tsx` | Both render the shared `ItemArchivePage` component, which echoes the slug. Two routes exist so legacy `/archive/` links keep working. |

There is no `/search` route. The PR description says it is in progress.

### Conventions the PR sets

- Shared code goes in `_components/`, `_styles/`, and `_utilities/` under `src/app`. The underscore keeps these folders out of routing.
- A component lives in the nearest folder shared by every route that uses it.
- Styling is plain CSS with native nesting and `@layer`. Tailwind utility classes are gone.

## Adverse implications

### Blocking

**1. The production build fails.** `src/app/browse/[[...slug]]/page.tsx` types `slug` as `string`, but an optional catch-all segment is `string[] | undefined`. `next build` stops at line 32. The page works under `npm run dev`, which does not type check, so the PR's own test steps pass. Merging would leave `main` unbuildable, and the Docker image (`RUN npm run build`) could not be built.

**2. Nothing automated reports the failure.** The repo's only PR workflow is the preview deploy, which runs only when the `Deploy preview` label is present. The PR has the `enhancement` label alone, so the job was skipped and the PR shows no failing check. Adding the label would start a preview deploy that fails at the Docker build.

**3. Lint fails with nine errors.** All nine are unescaped quotes and apostrophes in `src/app/accessibility/page.tsx` (`react/no-unescaped-entities`). The build does not run lint, so this blocks nothing today, but it will block the PR after lint is added to CI. The two warnings are an unused `useSearchParams` import in `SearchResults.tsx` and an `<img>` in the footer.

### Behaviour visible to users

**4. Header search leads to a 404 from every page.** The form submits to `/search`, which does not exist. The PR description states this as expected for now. If `main` is deployed anywhere public before the search PR lands, the most prominent control on the site is broken.

**5. Unknown browse URLs return a 200 page, not a 404.** `/browse/cats` and `/browse/anything/else` all render "Browse Everything". This is deliberate (see the comment in the file), but it means mistyped or stale links never fail, and crawlers can index unlimited duplicate URLs. Adding a canonical URL or a redirect to `/browse` is worth deciding before launch. The same applies to `/item/[slug]`, `/archive/[slug]`, and `/collection/[slug]`, which accept any slug until they are connected to data.

**6. Page content has no side gutter on small screens.** `<main>` is `width: 100%` with no padding, and its first `max-width` starts at 576px. Below that, text runs to the screen edges.

**7. Dark mode is half applied.** `globals.css` sets `color-scheme: light dark` and swaps the body colours, but the header and dropdowns hard-code white. On a dark-mode system the body turns dark while the header stays white. The search input keeps near-black text and has no background of its own, so its text is likely unreadable. Not reproduced.

**8. A click or Enter may close the dropdown that hover or focus just opened.** The trigger buttons keep the popover's default toggle action. After hover or keyboard focus opens the menu, the click or Enter that follows toggles it shut. Not reproduced. The PR's test steps list tap on the trigger as a way to dismiss, so part of this may be intended, but for a keyboard user Enter on a focused trigger would close the menu.

**9. The heading font never loads, and the body font depends on the footer.** Nothing loads `gineso-condensed`, so the site name and mobile menu headings fall back to a generic sans-serif. `Acherus` is declared only in `VTLibFooter.css` and fetched from `www.assets.cms.vt.edu` at run time. Replacing or removing the footer would drop the body font site-wide, and the site now depends on that host. Removing `next/font` also removes self-hosting and preloading, so text may visibly change font during load.

### Accessibility

**10. Accessibility testing is incomplete.** The PR's own checklist leaves the axe scan unchecked and describes screen-reader testing as spot checks, both deferred until header styling is final.

**11. The desktop footer logo link may have no accessible name.** At 768px and wider, the only logo link is an `<a>` inside an SVG marked `role="presentation"`, labelled only by a `title` attribute. Not reproduced. The footer is shared code, so a fix probably belongs upstream too.

### Browser support

**12. The header depends on very new CSS.** The dropdowns use anchor positioning (`position-area`, `position-try-fallbacks`), `@starting-style`, and discrete transitions; the layout uses the `<search>` element and the `scripting` media query. Commit `a5df849` removed `@scope` from this PR for being only newly available across browsers, and anchor positioning is at a similar level of support. The `@supports not` fallback in `Header.css` also uses `anchor()`, so it does not help browsers that lack anchor positioning; there the dropdown would open unpositioned. Not reproduced. The team should state which browsers the site supports and test the oldest one.

### Maintenance

**13. Header styles are attached to every `<header>` element.** `Header.css` uses the bare `header` selector with nested `button` rules. A later `<header>` inside an item or article page would pick up the site header's grid, border, and button styling.

**14. Tailwind is removed from the code but not from the build.** `tailwindcss` and `@tailwindcss/postcss` remain in `package.json`, and `postcss.config.mjs` still runs the plugin on every build. Anyone reading the config would assume Tailwind is in use. Removing the plugin later changes how the CSS is processed, so the pages need a visual check then.

**15. Layered and unlayered CSS are mixed.** `Header.css` and `SearchBar.css` are inside `@layer components`; `globals.css`, `CustomIcons.css`, and the footer are not. Unlayered rules always beat layered ones, whatever their specificity, so a future global rule for `button` or `a` would override the header's styles. The PR lists an `@layer` refactor as planned work.

**16. Both header hooks change the DOM directly.** They find elements by class name and set `hidden` and `aria-expanded` outside React. This works now, but renaming a class breaks the mobile menu with no error. The whole header is also a client component, as its own TODO notes.

**17. A 766-line copy of the VT Libraries footer now lives in this repo.** Updates to the shared footer will not arrive automatically, and the copy redefines colour tokens that `vars.css` already defines.

**18. Starter leftovers.**

- The site's meta description is still "Generated by create next app", which search engines and link previews will show.
- Five unused starter images remain in `public/`.
- Two empty stylesheets were added: `ItemArchivePage.css` and `browse/[[...slug]]/page.css`.
- The Accessibility page text has two typos carried over from production: "magnigication" and "glady".
- `/about/platform` exists but nothing links to it.

## Recommendation

Ask for the browse page type fix (item 1) and the lint fix (item 3) before approving. Both are small; `pr21-fixes.md` has the code for the first.

Items 4 to 9 are acceptable for a first layout PR only if `main` is not deployed publicly before follow-up work lands. It would help to have the author confirm which of them are planned, since the PR description already covers search (item 4) and the `@layer` refactor (item 15).

Separately from this PR, adding a workflow that runs `npm run build` and `npm run lint` on every pull request would have caught items 1 and 3.
