# Bug report (draft): `@aws-amplify/data-construct` bundles mismatched OpenTelemetry packages, breaking `npm ci`

**Where to file:** https://github.com/aws-amplify/amplify-backend/issues (or aws-amplify/amplify-category-api, which publishes data-construct)

---

### Description

Starting with `@aws-amplify/data-construct@1.17.4` (and the `@aws-amplify/graphql-api-construct` versions it depends on, e.g. 1.22.3), the published tarballs contain bundled dependencies that don't match each other's version requirements:

| Bundled package | Requires | Bundled version |
|---|---|---|
| `@opentelemetry/resources@2.0.0` | `@opentelemetry/core@2.0.0` (exact) | `@opentelemetry/core@2.8.0` |
| `@opentelemetry/sdk-trace-base@2.0.0` | `@opentelemetry/core@2.0.0` (exact) | `@opentelemetry/core@2.8.0` |

1.17.4 also bundles `@smithy/middleware-retry@3.0.34` (requires `uuid ^9.0.1`) alongside `uuid@11.1.1`.

Because of the mismatch, npm can't produce a lockfile that `npm ci` accepts. `npm install` writes the bundle as shipped, but `npm ci` resolves the dependencies itself, wants a nested `@opentelemetry/core@2.0.0`, and fails. Any project that depends on `@aws-amplify/backend` / `@aws-amplify/backend-data` 1.9.0 is affected, which breaks Amplify Gen 2 CI builds that run `npm ci`.

Overrides can't work around it: npm can't override bundled packages, and overriding `@opentelemetry/core` under data-construct sends npm into an endless `placeDep ... REPLACE` loop.

### Versions

- `@aws-amplify/backend` 1.25.1, `@aws-amplify/backend-data` 1.9.0 (requires data-construct `^1.17.7`)
- `@aws-amplify/data-construct` 1.17.4 – 1.17.8 broken; 1.17.0 and 1.17.3 OK
- `@aws-amplify/graphql-api-construct` 1.22.3 broken; 1.21.3 OK
- Reproduced on npm 10.9.4, 11.6.2, 11.19.1, 11.21.2, 12.2.2; Node 24.22.2; macOS

### Steps to reproduce

```sh
mkdir repro && cd repro && npm init -y
npm install -D @aws-amplify/backend@1.25.1 @aws-amplify/backend-cli aws-cdk-lib constructs
rm -rf node_modules
npm ci
```

Expected: `npm ci` installs from the lockfile `npm install` just wrote.

Actual (verified 2026-11-06 with npm 11.19.1, `--ignore-scripts`; output abridged):

```
npm error code EUSAGE
npm error `npm ci` can only install packages when your package.json and package-lock.json or npm-shrinkwrap.json are in sync.
npm error Missing: @opentelemetry/core@2.0.0 from lock file   (x4)
npm error Missing: @aws-cdk/toolkit-lib@1.19.0 from lock file
npm error Missing: @aws-cdk/cloud-assembly-api@2.2.0 from lock file
npm error Missing: archiver@7.0.1 from lock file
... (~65 more entries from inside the data-construct bundle)
```

The `@aws-cdk/toolkit-lib` and related entries look like a second mismatch: npm expects bundle contents that the lockfile written by `npm install` doesn't record. In our project, a lockfile that included those entries still failed on the four `@opentelemetry/core@2.0.0` entries.

To confirm from the tarball:

```sh
npm pack @aws-amplify/data-construct@1.17.8 && tar xzf aws-amplify-data-construct-1.17.8.tgz
grep '"version"\|"@opentelemetry/core"' package/node_modules/@opentelemetry/{core,resources}/package.json
```

### Suggested fix

Make the bundled OpenTelemetry versions agree before publishing: bundle `resources` / `sdk-trace-base` at 2.8.x to match `core@2.8.0`, or bundle `core@2.0.0`. A publish-time check such as `npm ls --all` inside the package would catch this kind of regression.

### Workaround

Pin the construct to the last release with a consistent bundle:

```json
"overrides": {
  "@aws-amplify/data-construct": "1.17.3"
}
```
