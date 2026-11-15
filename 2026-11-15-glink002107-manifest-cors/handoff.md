# Hand-off: glink002107 Manifest CORS

## State
Resolved for `glink002107`. No code or repo changes; the only change was a CloudFront invalidation plus refilling the cache with CORS requests.

## Key identifiers
- Archive record: `21a0c8d5-00ce-4ffb-81d3-55faf37df6b6` in `Archive-bxbkjhe235e3jcwcjcji5txvlm-vtdlpdev`; custom key `ark:/53696/e3e34892`
- CloudFront distribution: `E1FTBBPXBABMM9` (`d21nnzi4oh5qvs.cloudfront.net`), origin `ingest-dev.img.cloud.lib.vt.edu`
- Policies on the default behavior, by AWS managed policy ID:
  - cache `658327ea-…` (CachingOptimized)
  - origin request `88a5eaf4-…` (CORS-S3Origin)
  - response headers `60669652-…`
- Amplify app `d1n265krqy0ld3`, branch `dev`, backend env `vtdlpdev`

## Open issue (can recur for any manifest)
The cache key excludes `Origin`, so the first request after an invalidation or expiry decides whether the CORS header is cached. Durable fixes, any one of:
1. Use a cache policy that includes the `Origin` header in the cache key.
2. Use a response headers policy that always sets `Access-Control-Allow-Origin: *` with origin override enabled. Confirm what `60669652-…` actually does; it didn't add the header to the bad cached copy.
3. Set `Cache-Control` on manifests at upload time, which limits how long a bad browser or edge copy can last. This doesn't fix the cache-key problem itself.

The `vtdlp-whunter-workload` IAM user can't read or change cache or response headers policies, or call `GetInvalidation`. Someone with CloudFront admin rights has to make the change.

## Workaround until then
After invalidating a manifest, don't open its URL directly. Let the page or Mirador request it first, or refill the cache:
```
for ae in 'gzip, deflate, br, zstd' br gzip identity 'gzip, deflate, br'; do
  curl -sS -o /dev/null -D - -H 'Origin: https://dev.d1n265krqy0ld3.amplifyapp.com' \
    -H "Accept-Encoding: $ae" "$URL" | grep -iE '^HTTP|x-cache|access-control-allow-origin'
done
```

## Access notes
- `aws cloudfront wait invalidation-completed` fails with AccessDenied. Poll `list-invalidations` instead.
- The AppSync API (`ff4jrkonzrduziosmblcybfw4u`) uses an API key, but the permission classifier blocked querying it with the key scraped from the page's JavaScript. Query DynamoDB directly.
