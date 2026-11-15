# Session Summary: glink002107 Manifest CORS Failure (2026-11-15)

## Request
Mirador on the dev site (`https://dev.d1n265krqy0ld3.amplifyapp.com/archive/e3e34892`) failed to load the IIIF manifest `https://d21nnzi4oh5qvs.cloudfront.net/federated/glink/glink002107/manifest.json` with "No 'Access-Control-Allow-Origin' header". Two CloudFront invalidations and clearing the browser cache hadn't fixed it. Every other manifest in the collection loaded.

## Outcome
Fixed. The manifest now loads in Chrome from the archive page (200, CORS header present).

## Root cause
- Distribution `E1FTBBPXBABMM9` (origin bucket `ingest-dev.img.cloud.lib.vt.edu`) uses AWS's managed CachingOptimized cache policy, whose cache key does not include `Origin`.
- Whichever request fills the cache after an invalidation decides whether the CORS header is stored. If that request has no `Origin` header (for example, opening the manifest URL directly in a tab), the cached copy lacks `access-control-allow-origin`, and every later page request is served that copy and blocked.
- The bad copy (the `br`-compressed one Chrome gets) was cached at 17:59:58 UTC, about a minute after the user's second invalidation. The other manifests happened to be cached first by Mirador's CORS requests.
- Chrome's network listener reported the blocked request as status 503. Chrome itself recorded status 0 (blocked). CloudFront never returned a 503.

## Fix applied
1. Invalidated `/federated/glink/glink002107/manifest.json` (ID `IF59VKILXN84Z43LJQAM8HOJAF`).
2. Once it completed, requested the manifest with the site's `Origin` header for each compression type Chrome uses (`gzip, deflate, br, zstd`; `br`; `gzip`; `identity`; `gzip, deflate, br`). Every response had `access-control-allow-origin: *`.
3. Verified in Chrome: the archive page's request returns 200, and the manifest parses.

## What was ruled out
- A stale S3 object: there is one version, last modified 2026-08-27, with the same ETag CloudFront serves.
- Distribution config: no edge functions, firewall or custom error pages, and the config hasn't changed since 2024-02-26.
- S3 bucket CORS: allows `*` for GET, HEAD and POST.
- A service worker or app cache on the amplify site: none.
- Edge location: every edge from local DNS (IAD55) and from 1.1.1.1 (ATL58) returned 200 to curl.
- Object metadata: identical to the working `glink002106`.

## Lessons
- Reproduce browser failures in Chrome first and read the real request. Much time went into DynamoDB lookups and curl theories before that, and the user called this out.
- Plain curl tests can miss the bad cached copy, because CloudFront keeps a separate copy per compression type. Send Chrome's exact `Accept-Encoding` (`gzip, deflate, br, zstd`).
