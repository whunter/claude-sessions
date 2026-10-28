# PR #24 "Contact us padma012" — Code Review Findings

- **Branch:** `contact-us_padma012` -> `main`
- **Date:** 2026-10-27
- **Scope:** `git diff main...HEAD` (48 files, all 43 commits in the PR: layout/routing, fetchUtils, collection/item pages, dev:aws script, submitFeedback Lambda, /feedback form)
- **Method:** high-effort recall review, 8 angles (line-by-line, removed behavior, cross-file, reuse, simplification, efficiency, altitude, CLAUDE.md conventions), dedup only, no verification pass. Some findings may be false positives.
- **Nothing was posted to GitHub.**

Checks run locally: `npx tsc --noEmit` and `npx eslint src`. (`dompurify` is in package-lock but not installed in local node_modules, so its tsc error is just the local environment.)

## Findings (most severe first)

### 1. Browse page fails strict type-check, so `next build` fails
`src/app/browse/[[...slug]]/page.tsx:32` and `:38`

`params` is typed `Promise<{ slug: string }>`, but an optional catch-all gives `slug?: string[]`. `tsc` reports TS2345 (`slug?.at(0)` is `string | undefined`, passed to `includes(string)`) and TS7053 (`BrowseTypes[browseType]` indexed with a plain `string`). `tsconfig` has `strict: true` and `next.config.ts` doesn't set `ignoreBuildErrors`, so `next build` and the standalone Docker image fail.
**Fix:** type it as `{ slug?: string[] }` and type `BrowseTypes` as `Record<string, string>`, or narrow the key with `keyof typeof BrowseTypes`.

### 2. Lambda strips `\n` from the message, so every line break is lost
`src/app/_lambda/submitFeedback/index.js:103` (and `:245`)

`cleanMessage = sanitizeString(message)` uses the regex that removes `\r` **and `\n`**. That means `.replace(/\n/g, '<br>')` on line 245 never matches. A multi-paragraph report reaches DynamoDB and both email bodies as one run-on line. The frontend comment in `FeedbackForm.tsx:6` says it "Keeps \n so the user's line breaks and paragraphs are preserved", which the Lambda then undoes.
**Fix:** use a message-specific sanitizer that keeps `\n` (header-injection risk applies only to header fields such as Subject and the email addresses).

### 3. DOMPurify on plain text HTML-encodes it, so messages are double-escaped or lose text
`src/app/feedback/FeedbackForm.tsx:10` and `:17`

`DOMPurify.sanitize()` returns serialized HTML, so plain text gets entity-encoded: `"Search & browse < 2s"` becomes `"Search &amp; browse &lt; 2s"`. The Lambda then runs `escapeHtml` on it, so the email shows a literal `&amp;` and `&lt;`, and DynamoDB stores the encoded text. Markup that users quote in an accessibility report (`<button> has no label`) is changed or stripped. A message that is only markup (for example `<script>x</script>`) sanitizes to `""`, and the user gets "Missing required fields". The email field has the same problem (`a&b@x.com` becomes `a&amp;b@x.com`).
**Fix:** drop DOMPurify for these fields. The values are plain text, never rendered as HTML on the client, and the Lambda already escapes them for the HTML email. Removing it also removes the `dompurify` dependency.

### 4. Feedback page bakes `siteName` in at build time, and `""` makes every submission fail
`src/app/feedback/page.tsx:18`

`FeedbackPage` has no dynamic APIs, so Next statically prerenders it during `next build`. If AppSync is unreachable or its env vars are missing at build time, `getSite()` returns `null`. `siteName` is then baked in as `""`, and the Lambda rejects every submission with 400 "Missing required fields" (`index.js:124`) until the next rebuild. The intro text also reads "general feedback about ." in that case.
**Fix:** use a non-empty fallback such as "VT Digital Library Platform", and/or `export const dynamic = "force-dynamic"` (or `revalidate`).

### 5. `submittedBy` length is never enforced (`MAX_EMAIL_LENGTH` is unused)
`src/app/_lambda/submitFeedback/index.js:29` and `:185`

`MAX_EMAIL_LENGTH = 254` is declared, but nothing checks it, while message and siteName do get length checks. A direct curl POST with `submittedBy` set to a 300 KB `a...@x.com` passes the regex. Combined with the 5000-char message, it can exceed DynamoDB's 400 KB item limit (500 error), or it puts a huge value into the stored record and the email.
**Fix:** add `if (cleanSubmittedBy.length > MAX_EMAIL_LENGTH) return 400`.

### 6. Lambda returns internal SES error text to the public client, and the UI shows success when the email failed
`src/app/_lambda/submitFeedback/index.js:345` and `:361`

`emailError = emailErr.message` goes back in the 200 response body, even though the comment at lines 366-368 says error messages must not be sent to the client because they reveal account details. SES errors often include ARNs and identity addresses. Also, when the email fails the response is still `success: true`, and `FeedbackForm.tsx:153` tells the user the feedback was submitted, while the page says it will be "emailed to our team".
**Fix:** log `emailErr` only and return `emailSent: false` without the message.

### 7. Lambda logs the whole request event, including PII, to CloudWatch
`src/app/_lambda/submitFeedback/index.js:77`

`console.log('Received event:', JSON.stringify(event, null, 2))` writes every submitter's email, full message, source IP and headers to CloudWatch on every call, kept for the log group's retention period. Accessibility-barrier reports may contain disability-related information.
**Fix:** log only `event.requestContext.requestId` / `feedbackId`.

### 8. Missing `FEEDBACK_EMAIL_TO` config shows up as a client "Missing required fields" 400
`src/app/_lambda/submitFeedback/index.js:115` and `:124`

`cleanEmailTo` now comes from the Lambda env, not the request, but the "required fields" check still treats it as user input. If the env var is unset in a new environment (for example the pprd Lambda), users see "Error: Missing required fields" with every field filled in, and the cause looks like a client bug.
**Fix:** check `FEEDBACK_EMAIL_TO` separately and return a 500 with a logged config error.

### 9. Collection page runs independent GraphQL requests one after another
`src/app/collection/[slug]/page.tsx:25-26`

`getCollectionItems(collection.id)` and `getCollectionMap(collection, topLevel)` don't depend on each other, but they're awaited in sequence. That adds one full AppSync round-trip to every collection page render.
**Fix:** `const [{ items, total }, map] = await Promise.all([getCollectionItems(...), getCollectionMap(...)]);`

### 10. `npm run lint` fails: 9 `react/no-unescaped-entities` errors on the accessibility page
`src/app/accessibility/page.tsx:6`, `9`, `18`, `21`, `23`, `25`, `26`

Raw `'` and `"` in JSX text, for example `Virginia Tech's Accessibility Portal`. `npx eslint src` exits with 9 errors, so any CI lint gate fails. Also minor typos in the same file: "magnigication", "glady". There's an unused `useSearchParams` import in `src/app/_components/search/SearchResults.tsx:3`.
**Fix:** escape the characters (`&apos;`, `&quot;`) or use typographic quotes.

## Lower-priority notes (not in the top 10)
- `scripts/dev.mjs:25`: `process.exit(code ?? 0)` exits 0 when `next dev` is killed by a signal (`code` is `null`).
- `src/app/_utils/fetchUtils/getCollectionMap.ts:385`: the sort comparator never returns 0 (equal numbers give -1), which makes the order inconsistent for duplicate names or numbers.
- `src/app/_components/collection/CollectionOrganization.tsx:15`: the `slug !== "null"` special case belongs in `toSlug` (treat a literal "null" custom_key as empty), not in the component.
- `getCollectionDetails` uses `matchPhrase` on `custom_key`, while `getItemDetails` uses `eq`. Consider `eq` for an exact-key lookup with `limit: 1`.
- `FeedbackForm.tsx:140` still sends `emailTo`, which the Lambda deliberately ignores. This is dead payload.
- Empty CSS files were added: `src/app/_components/items/ItemArchivePage.css` and `src/app/browse/[[...slug]]/page.css`.
- `aws-sdk` v2 (Lambda) is end-of-life. Consider `@aws-sdk/client-ses` and `@aws-sdk/lib-dynamodb` v3.

## Conventions (CLAUDE.md)
No repo-level or directory-level CLAUDE.md exists. The rules in the user-level `~/.claude/CLAUDE.md` cover commit and PR attribution and session workflow, not code. No violations were found in the diff.

## JSON
```json
[
  {"file":"src/app/browse/[[...slug]]/page.tsx","line":32,"summary":"Optional catch-all params typed as { slug: string } plus an untyped BrowseTypes index fail strict tsc (TS2345, TS7053), so next build fails.","failure_scenario":"next build / Docker standalone build runs type-check under strict: true, the build errors out and nothing deploys."},
  {"file":"src/app/_lambda/submitFeedback/index.js","line":103,"summary":"sanitizeString strips \\n from the message, so the later \\n to <br> replace never matches and all line breaks are lost.","failure_scenario":"User submits a 3-paragraph report; DynamoDB and both email bodies get one run-on line."},
  {"file":"src/app/feedback/FeedbackForm.tsx","line":10,"summary":"DOMPurify.sanitize on plain text HTML-encodes & and < and strips or changes quoted markup, which the Lambda then double-escapes.","failure_scenario":"Message 'Search & browse < 2s' arrives in the email as 'Search &amp; browse &lt; 2s'; a message of only '<script>x</script>' becomes empty and gets 400 Missing required fields."},
  {"file":"src/app/feedback/page.tsx","line":18,"summary":"Statically prerendered page bakes siteName at build time; a getSite failure falls back to '' and the Lambda rejects every submission.","failure_scenario":"AppSync unreachable or env missing during next build, siteName='' is baked in, and every submit returns 400 'Missing required fields' until rebuild."},
  {"file":"src/app/_lambda/submitFeedback/index.js","line":185,"summary":"MAX_EMAIL_LENGTH is declared but submittedBy length is never checked.","failure_scenario":"curl POST with a 300KB submittedBy passes validation and is stored or emailed, or exceeds DynamoDB's 400KB item limit and returns 500."},
  {"file":"src/app/_lambda/submitFeedback/index.js","line":361,"summary":"Raw SES error message is returned to the public client, contradicting the file's own no-leak rule, and the client shows success when the email failed.","failure_scenario":"SES rejects the send; the response body includes emailError with identity or ARN details, and the user is told the feedback was submitted although no one was emailed."},
  {"file":"src/app/_lambda/submitFeedback/index.js","line":77,"summary":"The whole API Gateway event (submitter email, message, IP, headers) is logged to CloudWatch on every call.","failure_scenario":"Every accessibility-barrier report with personal and disability details is kept in CloudWatch logs for the retention period."},
  {"file":"src/app/_lambda/submitFeedback/index.js","line":124,"summary":"A missing FEEDBACK_EMAIL_TO server config is reported as a client 400 'Missing required fields'.","failure_scenario":"New pprd Lambda without the env var: users with every field filled see 'Missing required fields', which looks like a frontend bug."},
  {"file":"src/app/collection/[slug]/page.tsx","line":25,"summary":"getCollectionItems and getCollectionMap are independent but awaited sequentially.","failure_scenario":"Each collection page render waits for an extra AppSync round-trip; Promise.all would run them in parallel."},
  {"file":"src/app/accessibility/page.tsx","line":6,"summary":"Unescaped ' and \" in JSX give 9 react/no-unescaped-entities errors, so npm run lint fails.","failure_scenario":"npx eslint src exits non-zero, which fails any CI lint gate."}
]
```
