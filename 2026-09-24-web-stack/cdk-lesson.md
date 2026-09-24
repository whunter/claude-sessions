# How the CDK scripts work: one command, traced end to end

This lesson follows a single command through every program it touches, from the moment you press Enter to a request landing on DynamoDB. Every file reference is relative to the repo root, `~/dev/dlp/access/dlp-access-next-cdk`. The command outputs and template excerpts are real: they were produced by running the commands against branch `whunter/multi-env` at `c9e6b85`.

The command we trace is the largest one, the one that provisions a feature environment and a branch deployment together:

```bash
cd infra
npx cdk deploy --all -c env=f-search -c branch=whunter/multi-env -c backend=provision
```

The other modes are subsets of this one. They're covered in [Step 11](#step-11-the-other-modes).

---

## The big picture

Five separate programs take part, and each one hands its output to the next:

```
 you ──► (1) cdk CLI ──spawns──► (2) your TypeScript app (bin/appsync.ts)
                                        │  builds objects in memory, writes
                                        ▼  JSON files; never talks to AWS
                                  infra/cdk.out/  (templates + assets + manifest)
                                        │
          (1) cdk CLI ◄─────────────────┘  reads cdk.out, uploads, calls AWS
                │
                ▼
         (3) CloudFormation  ── creates/updates resources, one stack at a time
                │
                ▼
         (4) Elastic Beanstalk ── launches an EC2 instance for the Web stack
                │
                ▼
         (5) the platform's hook on that instance ── npm ci && next build, then next start
```

The most important idea in CDK is the split between **synth time** and **deploy time**.

- **Synth time** is steps 1 and 2. Your TypeScript runs on your laptop and produces CloudFormation JSON. It has no AWS credentials (it doesn't need any) and it can't see anything that exists in AWS yet.
- **Deploy time** is steps 3 to 5. AWS reads that JSON and makes it real.

Many CDK puzzles make sense once you ask which side of that line something happens on. Two examples:

- A table's ARN doesn't exist while your TypeScript is running.
- The SSM parameter the Web stack reads is only looked up by CloudFormation.

---

## Step 1: the `cdk` CLI reads `infra/cdk.json`

`npx cdk` runs the CLI from `infra/node_modules/aws-cdk`, the `aws-cdk` devDependency in `infra/package.json`. The first thing it does is look in the current directory for `cdk.json`. That lookup is why every command must be run from `infra/`; from anywhere else you get "`--app is required`".

`infra/cdk.json` has two parts that matter.

```json
"app": "npx ts-node --prefer-ts-exts bin/appsync.ts",
```

This is **the command that produces your infrastructure**. The CLI doesn't know anything about your stacks. It only knows how to run this command and read what it writes. `ts-node` runs TypeScript directly, with no separate `tsc` step.

```json
"context": {
  "@aws-cdk/core:defaultCrossStackReferences": "strong",
  "@aws-cdk/aws-iam:minimizePolicies": true,
  ...
}
```

This is **context**, a key/value bag your app can read. The entries here are *feature flags*. They opt into newer CDK behaviours, such as merging IAM statements (`minimizePolicies`). They're fixed per project, so upgrading CDK doesn't silently change your templates.

Then the CLI merges your `-c key=value` flags into that same bag. For our command, the context the app will see is:

```
env      = "f-search"
branch   = "whunter/multi-env"
backend  = "provision"
+ the feature flags from cdk.json
```

> `-c` is just "add a context value". CDK gives `env`, `branch` and `backend` no special meaning; this project's own code interprets them (Step 3).

## Step 2: the CLI spawns your app

The CLI runs the `app` command as a **child process**. It passes two things through environment variables:

- `CDK_CONTEXT_JSON`: the merged context from Step 1.
- `CDK_OUTDIR`: where to write output, which is `infra/cdk.out` by default or the path given with `-o`.

That's the entire interface between the CLI and your code: environment variables in, files out. When your code throws, you see the child process die with its stack trace:

```
$ npx cdk ls
Error: Missing CDK context: pass -c env=<name>, one of dev, pre-production, production or f-<slug>
npx ts-node --prefer-ts-exts bin/appsync.ts: Subprocess exited with error 1
```

## Step 3: `infra/bin/appsync.ts`, the entry point

```ts
const app = new cdk.App();
const context = (key: string) => app.node.tryGetContext(key);
buildApp(app, { env: context('env'), branch: context('branch'), backend: context('backend') });
```

1. `new cdk.App()` creates the **root of the construct tree**. It reads `CDK_CONTEXT_JSON` and `CDK_OUTDIR`. It also registers a hook that runs `app.synth()` automatically when the Node process is about to exit. That's why no file ever calls `synth()`.
2. `tryGetContext` reads one key from the context, returning `undefined` if it isn't set. It's the only place the `-c` flags enter the code.
3. `buildApp` does the real work. It lives in `infra/lib/app.ts` rather than in `bin/` so the Jest tests can call it directly with plain arguments (Step 12).

## Step 4: `buildApp` decides which stacks exist (`infra/lib/app.ts:34`)

### 4a. Resolve the environment

```ts
const config = resolveEnvironment(options.env);
```

`resolveEnvironment` (`infra/lib/environments.ts`) turns the string `"f-search"` into an `EnvironmentConfig` object:

1. **Missing?** It throws "Missing CDK context".
2. **Bad shape?** The name must match `/^[a-z][a-z0-9-]{0,19}$/`. The 20-character limit exists because the OpenSearch domain is `dlpnext-<env>` and domain names max out at 28 characters.
3. **Lookup**: `dev`, `pre-production` and `production` are entries in `ENVIRONMENTS`. Anything starting with `f-` gets the `FEATURE` settings, which are dev's settings with `removalPolicy: DESTROY`. Anything else throws "Unknown environment".
4. **Production guard**: production's account is the placeholder `PRODUCTION_ACCOUNT_ID`, so it throws until someone fills in the real ID.

For `f-search` the result is:

```ts
{ name: 'f-search', account: '226388486048', region: 'us-east-1',
  search: { instanceType: 't3.small.search', dataNodes: 1, availabilityZones: 1, volumeSizeGiB: 10 },
  web: { instanceType: 't3.small' },
  removalPolicy: RemovalPolicy.DESTROY }
```

Every setting that differs between environments is in this one object. The stacks never check `if (env === 'production')`; they only read `config`.

### 4b. Validate the mode flags

```ts
if (options.branch === undefined && options.backend !== undefined) throw ...  // backend without branch
const backend = options.backend ?? 'attach';                                   // default
if (!BACKENDS.includes(backend)) throw ...                                     // typo guard
```

### 4c. Pick the stacks

```ts
const provision = options.branch === undefined || backend === 'provision';
```

| Flags | `provision` | Stacks created |
| --- | --- | --- |
| `-c env=dev` | true (no branch) | Data, Api |
| `-c env=dev -c branch=X` | false (attach) | Web |
| `-c env=f-search -c branch=X -c backend=provision` | true | Data, Api, Web |

You can check this without deploying anything. `cdk ls` runs Steps 1 to 4 and prints the stack names:

```
$ npx cdk ls -c env=dev
DlpAccessNext-dev-Data
DlpAccessNext-dev-Api

$ npx cdk ls -c env=dev -c branch=whunter/Multi_Env
DlpAccessNext-Web-whunter-multi-env

$ npx cdk ls -c env=f-search -c branch=whunter/multi-env -c backend=provision
DlpAccessNext-f-search-Data
DlpAccessNext-f-search-Api
DlpAccessNext-Web-whunter-multi-env
```

Note the second example: `whunter/Multi_Env` became `whunter-multi-env`. That's `branchSlug` in `infra/lib/web-stack.ts`, which lowercases the name and turns every run of non-alphanumeric characters into `-`.

### 4d. Construct the stacks

```ts
data = new DataStack(app, `${prefix}-Data`, { env, config });
api  = new ApiStack(app, `${prefix}-Api`, { env, config, tables: data.tables, searchDomain: data.searchDomain });
web  = new WebStack(app, `DlpAccessNext-Web-${branch}`, { env, config, branch });
if (api) web.addStackDependency(api);
```

Each `new XStack(app, id, props)` runs that class's constructor, which is where all the resources are declared. Before looking at them, you need two core ideas.

---

## Interlude: constructs and tokens

### The construct tree

Every CDK object is a **construct**, created as `new Thing(scope, id, props)`. The `scope` is its parent, so the objects form a tree:

```
App
├── DlpAccessNext-f-search-Data          (Stack)
│   ├── ArchiveTable                     (dynamodb.Table)
│   │   └── Resource                     (CfnTable  ← an actual CloudFormation resource)
│   ├── SearchDomain ...
├── DlpAccessNext-f-search-Api
│   ├── VtdlpApi
│   │   ├── ArchiveDataSource ...
└── DlpAccessNext-Web-whunter-multi-env
    ├── SourceBundle, Application, Version, ServiceRole, Environment
```

Constructs come in levels:

- **L1** (`Cfn*`, e.g. `CfnEnvironment`) map one-to-one onto CloudFormation resource types. You set every property yourself.
- **L2** (e.g. `dynamodb.Table`, `iam.Role`) wrap an L1 with defaults and helper methods such as `grant*` and `addEventSource`. One L2 can emit several resources.

The Web stack uses L1s for Elastic Beanstalk, because CDK has no L2 for it. The other stacks are almost all L2.

Each resource's **logical ID** in the template is its tree path plus a hash, for example `ServiceRole4288B192`. That ID is how CloudFormation matches a resource between deploys. **Changing a construct's `id` or moving it in the tree makes CloudFormation delete the old resource and create a new one.** For the retained tables, that would mean an orphaned table and a name clash.

The whole tree, as synthesized, is written to `cdk.out/tree.json` if you want to browse it.

### Tokens: placeholders for values that don't exist yet

In the Api stack, `api.graphqlUrl` looks like a string. At synth time, though, there is no API, so there is no URL. What you actually hold is a **token**, a placeholder string such as `${Token[TOKEN.123]}`. During synthesis CDK replaces it with the CloudFormation expression that will produce the value at deploy time, here `{"Fn::GetAtt": ["VtdlpApi…", "GraphQLUrl"]}`.

Consequences:

- You can pass tokens around and put them into other resources' properties freely.
- You **can't** inspect them in TypeScript. `if (api.graphqlUrl.startsWith('https'))` would test the placeholder, not the URL.
- When a token from **one stack** is used in **another**, CDK does extra work (Step 5b).

---

## Step 5: the stack constructors

### 5a. `DataStack` (`infra/lib/data-stack.ts`): the stateful half

**Tables** (line 34). It loops over `MODELS` from `infra/lib/models.ts`, the seven model names, and creates one `dynamodb.Table` for each:

- Named by `tableName(model, env)`, for example `Archive-dlpnext-f-search`. The `<Model>-` prefix matters, because the streaming Lambda derives the OpenSearch index name from it.
- Hash key `id`, on-demand billing, `NEW_AND_OLD_IMAGES` streams.
- The GSIs listed in `GLOBAL_INDEXES`.
- `deletionProtection` and PITR on when `removalPolicy` is RETAIN, so on for dev, pre-production and production and off for `f-*`.

**OpenSearch domain** (line 59). Its sizing comes straight from `config.search`.

**Index template custom resource** (lines 85–104). CloudFormation can't configure anything *inside* an OpenSearch domain. To do that, the stack defines:

- a Python Lambda (`infra/lambda/opensearch-index-template/index.py`);
- a `cr.Provider`, CDK's framework that turns a Lambda into a CloudFormation custom-resource handler;
- a `CustomResource`.

At deploy time CloudFormation calls the Lambda with `RequestType: Create`, and the Lambda PUTs an index template (`auto_expand_replicas: 0-1`) into the domain. The resource is ordered after the domain because its Lambda's environment references `domain.domainEndpoint`, a token.

**Public fields.** The stack exposes `this.tables` and `this.searchDomain` as properties, so `buildApp` can pass them to the Api stack.

Synthesized: 16 resources (7 tables, 1 domain, 2 Lambdas, their roles and policies, and the custom resource).

### 5b. `ApiStack` (`infra/lib/api-stack.ts`): the stateless half

**The API** (line 42) reads `infra/schema/schema.graphql` from disk *at synth time* and embeds it in the template, with IAM as the only auth mode.

**Data sources** (line 58). `api.addDynamoDbDataSource('ArchiveDataSource', tables.Archive)` does three things:

1. It creates an AppSync data source pointing at the table.
2. It creates an IAM role that AppSync assumes.
3. It grants that role read/write on the table.

**Here is the cross-stack reference.** `tables.Archive` belongs to the *Data* stack, but it's being used in the *Api* stack. CDK notices that a token crossed a stack boundary, and does three things automatically:

1. It adds an **Output with an Export** to the Data template:
   ```
   ExportsOutputRefArchiveTable4E5864BF16DAEC2E
     → Export name "DlpAccessNext-f-search-Data:ExportsOutputRefArchiveTable4E5864BF16DAEC2E"
   ```
2. It writes an **`Fn::ImportValue`** where the Api template needs the value (real synthesized output):
   ```json
   "DynamoDBConfig": {
     "AwsRegion": "us-east-1",
     "TableName": { "Fn::ImportValue": "DlpAccessNext-f-search-Data:ExportsOutputRefArchiveTable4E5864BF16DAEC2E" }
   }
   ```
3. It adds a **stack dependency** of Api on Data, so Data always deploys first.

The Data template ends up with 18 such exports: table names, table ARNs, stream ARNs, and the domain ARN and endpoint.

> **Why exports are "strong" coupling.** CloudFormation won't let you delete or change an export while another stack imports it. That's great for safety between Data and Api. It would be a problem for Web stacks, which come and go per branch and may be deployed from a different CDK run. So the Web stack deliberately doesn't use this mechanism (5c).

**Resolvers** (lines 64–166). `jsResolver(...)` creates an `appsync.Resolver` whose code is a **string generated in TypeScript**. `getByIdCode()` in `infra/lib/resolvers.ts` returns APPSYNC_JS source, and that string is copied verbatim into the template:

```json
"QuerygetArchiveResolverF3D41FAD": {
  "Code": "import { util } from '@aws-appsync/utils';\n\nexport function request(ctx) {\n  return { operation: 'GetItem', key: util.dynamodb.toMapValues({ id: ctx.args.id }) };\n}\n...",
  "DataSourceName": "ArchiveDataSource", "FieldName": "getArchive", "TypeName": "Query",
  "Runtime": { "Name": "APPSYNC_JS", "RuntimeVersion": "1.0.0" }
}
```

So a resolver has two lives. It's *generated* on your laptop at synth time, and it *runs* inside AppSync at request time. A mistake in the generator can't show up until deploy time, when AppSync validates the code ("The code contains one or more errors").

**Streaming Lambda** (lines 170–207). This is a Python function packaged from `infra/lambda/opensearch-streaming/`, with `tests` and `__pycache__` excluded. `streamingFn.addEventSource(new DynamoEventSource(table, {...}))` becomes an `AWS::Lambda::EventSourceMapping`. That resource is AWS's poller that reads the table's stream and invokes the function. Its source ARN is again an import from Data:

```json
"EventSourceArn": { "Fn::ImportValue": "DlpAccessNext-f-search-Data:ExportsOutputFnGetAttArchiveTable4E5864BFStreamArnE412492B" },
"BatchSize": 100, "MaximumRetryAttempts": 3, "BisectBatchOnFunctionError": true,
"DestinationConfig": { "OnFailure": { "Destination": { "Fn::GetAtt": ["OpenSearchStreamingFailures…", "Arn"] } } },
"StartingPosition": "LATEST"
```

The `grantPathReadWrite` and `grantIndexReadWrite` calls give the function's role IAM permission on the domain's `_bulk` path and on the `archive` and `collection` indices.

**The Beanstalk instance role** (lines 215–229). This is an IAM role named `dlp-access-next-f-search-eb` plus an instance profile with the same name. `api.grant(ebRole, IamResource.all(), 'appsync:GraphQL')` adds a policy allowing the role to call the API. Every branch that attaches to `f-search` runs its EC2 instance with this profile.

**The hand-off to Web stacks** (line 233):

```ts
new ssm.StringParameter(this, 'GraphQLApiUrlParameter', {
  parameterName: graphqlApiUrlParameterName(config.name),   // "/dlp-access-next/f-search/graphql-api-url"
  stringValue: api.graphqlUrl,                              // token → Fn::GetAtt at deploy time
});
```

At deploy time this writes the real URL to a well-known SSM parameter name.

Synthesized: 68 resources, 26 of them resolvers.

### 5c. `WebStack` (`infra/lib/web-stack.ts`): one branch of the Next.js app

**The source bundle** (line 49):

```ts
this.sourceBundle = new s3assets.Asset(this, 'SourceBundle', {
  path: REPO_ROOT, ignoreMode: IgnoreMode.GIT, exclude: [...gitignore, ...BUNDLE_EXCLUDES],
});
```

An **asset** is a local file or directory that CDK will upload to S3 at deploy time. At synth time CDK:

1. copies the repo root, minus the excludes, into `cdk.out/asset.<hash>/`;
2. computes a hash of the contents;
3. hands you tokens for the future bucket and key (`s3BucketName`, `s3ObjectKey`).

The real staged copy (376 KB) contains:

```
.gitignore  .platform/  eslint.config.mjs  next.config.ts  package-lock.json
package.json  postcss.config.mjs  public/  src/  tsconfig.json
```

It has no `node_modules`, `.next`, `infra` or `.env*`. The key is the content hash (`3fa7f6a6….zip`), so **if the source didn't change, the key doesn't change and nothing is redeployed**.

**Application and version** (lines 55–66). These are L1 resources. `CfnApplicationVersion` points at the asset's bucket and key. `addResourceDependency(application)` adds a CloudFormation `DependsOn`. It's needed because the version refers to the application by a *plain string name*, not a token, so CDK can't infer the ordering.

**Service role** (line 70). This is the role Beanstalk *itself* assumes to manage the environment (health checks, managed platform updates). It's a different role from the instance role, which is what the *app* runs as. The `service-role/` prefix on the enhanced-health policy ARN was this session's deploy bug.

**The API URL, without a cross-stack reference** (line 80):

```ts
const apiUrl = ssm.StringParameter.valueForStringParameter(this, graphqlApiUrlParameterName(config.name));
```

This doesn't read SSM at synth time; remember, synth has no AWS access. It emits a **CloudFormation parameter of the special type `AWS::SSM::Parameter::Value<String>`**:

```json
"Parameters": {
  "SsmParameterValuedlpaccessnextfsearchgraphqlapiurl…Parameter": {
    "Type": "AWS::SSM::Parameter::Value<String>",
    "Default": "/dlp-access-next/f-search/graphql-api-url"
  }
}
```

It uses `{"Ref": "<that parameter>"}` wherever the URL is needed. CloudFormation resolves the value when it prepares each deploy of this stack (Step 8). The Web template therefore contains **no `ImportValue`**. It only knows *names*: this SSM path, and the instance profile name `dlp-access-next-f-search-eb` as a literal string. That is what lets a Web stack attach to an environment deployed last month, from a different CDK command.

**Option settings** (lines 82–123). The `settings` object is grouped by Beanstalk namespace for readability. `flatMap` then flattens it into the list shape CloudFormation wants. Synthesized:

```json
{ "Namespace": "aws:autoscaling:launchconfiguration", "OptionName": "IamInstanceProfile", "Value": "dlp-access-next-f-search-eb" },
{ "Namespace": "aws:elasticbeanstalk:application:environment", "OptionName": "APPSYNC_API_URL",
  "Value": { "Ref": "SsmParameterValuedlpaccessnextfsearchgraphqlapiurl…Parameter" } },
{ "Namespace": "aws:elasticbeanstalk:environment", "OptionName": "ServiceRole",
  "Value": { "Fn::GetAtt": ["ServiceRole4288B192", "Arn"] } },
...
```

The `aws:elasticbeanstalk:application:environment` namespace is how Beanstalk sets environment variables for the app process. That's how `APPSYNC_API_URL` reaches `process.env` in `src/lib/appsync.ts`.

**Outputs.** `EnvironmentName` and `EndpointUrl` are printed at the end of the deploy.

**Back in `buildApp`: `web.addStackDependency(api)`.** Because the Web stack doesn't reference the Api stack through tokens, CDK sees no link between them. Without this line, `cdk deploy --all` could deploy Web first, and CloudFormation would fail with "Unable to fetch parameters" because the SSM parameter doesn't exist yet. In attach mode `api` is `undefined`, so no dependency is added, and the Api stack must already exist from an earlier deploy.

Synthesized: 5 resources.

---

## Step 6: synthesis writes `cdk.out`

When `buildApp` returns, `bin/appsync.ts` has nothing left to do, and Node is about to exit. The auto-synth hook from Step 3 fires, and `app.synth()` does the following:

1. It runs validation, and throws for things like a missing required property or a construct-ID clash.
2. It walks the tree, resolves every token into a CloudFormation expression, and generates the automatic exports and imports.
3. It stages assets into `cdk.out/asset.<hash>/`.
4. It writes one template per stack, plus the manifest.

Real contents after the provision synth:

```
cdk.out/
├── manifest.json                                   ← the index the CLI reads
├── tree.json                                       ← the construct tree
├── DlpAccessNext-f-search-Data.template.json       ← CloudFormation
├── DlpAccessNext-f-search-Data.assets.json         ← what to upload where
├── DlpAccessNext-f-search-Api.template.json
├── DlpAccessNext-f-search-Api.assets.json
├── DlpAccessNext-Web-whunter-multi-env.template.json
├── DlpAccessNext-Web-whunter-multi-env.assets.json
├── asset.3fa7f6a6…/        (376K)  the Next.js source bundle
├── asset.e16ffb3b…/        (24K)   streaming Lambda code
├── asset.f689823c…/ asset.2819…/ asset.4810…/      index-template Lambda, cr.Provider framework, etc.
└── *.metadata.json, validation-report.json
```

The manifest records the dependency graph (real):

```
DlpAccessNext-f-search-Data           deps: [Data.assets]
DlpAccessNext-f-search-Api            deps: [DlpAccessNext-f-search-Data, Api.assets]      ← inferred from the tokens
DlpAccessNext-Web-whunter-multi-env   deps: [DlpAccessNext-f-search-Api, Web.assets]       ← from addStackDependency
```

In attach mode, the Web stack's only dependency is its own assets.

The manifest also names the **bootstrap** resources every deploy uses: `cdk-hnb659fds-assets-226388486048-us-east-1` (an S3 bucket) and roles such as `cdk-hnb659fds-deploy-role-…`. They were created once per account and region by `cdk bootstrap`. `hnb659fds` is CDK's default "qualifier".

The TypeScript child process then exits. **Everything after this point is the CLI and AWS; your code doesn't run again.**

## Step 7: the CLI deploys, stack by stack

Back in the parent `cdk` process, `deploy --all` reads `manifest.json` and deploys the stacks in dependency order: Data, then Api, then Web, one at a time by default. For each stack:

1. **Publish assets.** For each entry in `<stack>.assets.json`, it zips the `asset.<hash>` directory if needed and uploads it to the bootstrap bucket as `<hash>.zip`, assuming the `file-publishing-role`. If the key already exists (same hash), the upload is skipped. The template itself is uploaded the same way.
2. **Create a change set.** Assuming the `deploy-role`, it asks CloudFormation to compare the new template with what's deployed. This is the diff that `cdk diff` shows you.
3. **Execute it.** CloudFormation makes the changes, acting as the `cfn-exec-role` (which has broad permissions in the account). The CLI polls the stack's events and prints the progress lines you see.
4. **Print outputs** such as `GraphQLApiUrl` and `EndpointUrl`.

If a stack fails, the CLI stops. Stacks after it aren't attempted.

## Step 8: what CloudFormation does in each stack

CloudFormation builds its own dependency graph *inside* each template, from `Ref`, `Fn::GetAtt` and `DependsOn`. It creates independent resources in parallel.

**`DlpAccessNext-f-search-Data`**

- The seven tables are created in parallel, in seconds.
- The OpenSearch domain is the slow part, typically 15 to 30 minutes.
- Once the domain is up, CloudFormation creates the `IndexTemplate` custom resource. It invokes the provider Lambda, which invokes `index.py` with `RequestType: Create`. The Python code signs a request with its role's credentials and PUTs `_index_template/dlpnext-defaults`. When that succeeds, the stack is `CREATE_COMPLETE` and its 18 exports now hold real values.

**`DlpAccessNext-f-search-Api`**

- Every `Fn::ImportValue` resolves to Data's actual values.
- The API is created, then the schema, then the data sources, then the 26 resolvers. At this point AppSync validates each resolver's code.
- The Lambda is created, and the event source mappings start polling the table streams from `LATEST`.
- The EB role and instance profile are created.
- The SSM parameter `/dlp-access-next/f-search/graphql-api-url` is written with the real URL.

**`DlpAccessNext-Web-whunter-multi-env`**

1. **Before any resource is touched**, while it prepares the change set, CloudFormation resolves the SSM-typed parameter by reading `/dlp-access-next/f-search/graphql-api-url`. If the parameter isn't there, the deploy fails immediately with "Unable to fetch parameters". That's the attach-mode error the README warns about.
2. The `Application` and the `ServiceRole` are created (in parallel).
3. The `Version` is created after the application (`DependsOn`). It points at `s3://cdk-hnb659fds-assets-…/3fa7f6a6….zip`.
4. The `Environment` is created. CloudFormation now hands over to Beanstalk and waits, often for 5 to 10 minutes, until Beanstalk reports the environment as ready.

**Re-deploying** runs the same pipeline, and the change set contains only what differs:

- If only the Next.js source changed, the asset hash changes. The `Version` resource is replaced and the `Environment` is updated to the new version label. Beanstalk then redeploys onto the instance.
- If nothing changed, the CLI reports "no changes" and CloudFormation isn't asked to do anything.
- If the Api stack were rebuilt with a new URL, the Web stack would **not** notice by itself. The SSM value is read only when *the Web stack* deploys. Redeploy the Web stack to pick it up.

## Step 9: inside Elastic Beanstalk and on the instance

This part isn't CDK at all, but it's where the Web stack's settings take effect.

1. **Beanstalk assumes the service role**, then creates the underlying pieces: an Auto Scaling group of size 1 (SingleInstance), a security group, and an Elastic IP. The `EndpointUrl` output is this environment's CNAME, `dlpnext-whunter-multi-env.eba-….elasticbeanstalk.com`.
2. **The EC2 instance launches** as a `t3.small` on the pinned platform, `64bit Amazon Linux 2023 v6.11.8 running Node.js 24`. It has the instance profile `dlp-access-next-f-search-eb` attached, and IMDSv1 is disabled, so only token-based IMDSv2 can fetch credentials.
3. **The deploy engine on the instance** downloads the source zip and extracts it to `/var/app/staging`.
4. **The prebuild hook runs.** Beanstalk executes every file in `.platform/hooks/prebuild/`, which here is `01_build.sh`:
   ```bash
   cd /var/app/staging
   npm ci
   npm run build     # next build
   ```
   It must be executable. The CDK asset zip keeps file modes from your working tree, so the executable bit survives.
5. **The platform starts the app** with `npm start`, which runs `next start`. It sets the environment variables from the option settings, so `APPSYNC_API_URL` holds the real URL and `AWS_REGION` is `us-east-1`. nginx on the instance proxies port 80 to the Node process.
6. **Health.** Enhanced health reporting turns Green, and CloudFormation's wait from Step 8 ends. Logs stream to CloudWatch with 7-day retention.

## Step 10: a request at runtime

With everything up, a request to `http://<CNAME>/examples/appsync-queries` takes this path:

```
browser ──HTTP──► nginx ──► next start (server component)
                               │  src/lib/appsync.ts:
                               │  - URL from process.env.APPSYNC_API_URL
                               │  - credentials from the Node credential chain
                               │    → instance metadata → role dlp-access-next-f-search-eb
                               │  - SigV4-signs the POST (aws4fetch)
                               ▼
                          AppSync (IAM auth: does this role have appsync:GraphQL? yes, api.grant)
                               │  runs the generated resolver code for e.g. Query.getArchive
                               ▼
                          ArchiveDataSource (assumes its own role) ──► DynamoDB GetItem on Archive-dlpnext-f-search
```

Search queries (`fulltextArchives` and `searchObjects`) go to the OpenSearch data source instead. The data is kept in sync by the write path:

```
write to Archive-dlpnext-f-search ──► DynamoDB stream ──► event source mapping ──► streaming Lambda
    ──► POST _bulk to index "archive" on dlpnext-f-search
    (failures: 3 retries, batch split in half, then the record goes to the SQS failure queue)
```

---

## Step 11: the other modes

**`-c env=dev`** (no branch). Only Steps 5a and 5b run. You get two stacks, and Api depends on Data through the exports. This is how an environment is created or updated.

**`-c env=dev -c branch=X`** (attach, the default). Only Step 5c runs, and the app contains only the Web stack. No dependency is added, so correctness relies entirely on *names*:

- the SSM parameter `/dlp-access-next/dev/graphql-api-url`, checked when the Web stack is deployed;
- the instance profile `dlp-access-next-dev-eb`, checked by Beanstalk when it launches the instance.

**`--all` in attach mode.** `--all` means "every stack *in this synthesized app*". In attach mode that's just the Web stack, so the dev Data and Api stacks can't be touched.

**Repointing a branch.** Deploying the same branch with `-c env=pre-production` produces the *same stack name*, because the name depends only on the branch. The only template differences are:

- the SSM parameter's default path;
- the instance profile string;
- the environment name in the application description.

CloudFormation updates the environment in place, and it relaunches the instance with the new profile.

**Destroy.** `cdk destroy DlpAccessNext-Web-X -c env=dev -c branch=X` still runs Steps 1 to 6, because the CLI needs the synthesized app to know which stacks exist. It then asks CloudFormation to delete the stack. Two things behave differently for the environment stacks:

- **Destroying Data before Api fails**, because Api still imports Data's exports. That's the strong coupling from 5b doing its job. Web stacks have no exports and no imports, so they can be deleted at any time.
- **For dev, pre-production and production**, tables and the domain have `RemovalPolicy.RETAIN`. CloudFormation removes them from the stack but **leaves the actual resources** in the account. For `f-*` environments they're deleted.

## Step 12: how the tests use the same pipeline

`infra/test/app.test.ts` skips the CLI entirely:

```ts
const { data, api } = buildApp(new App(), { env: 'dev' });
const template = Template.fromStack(api!);
template.hasResourceProperties('AWS::AppSync::Resolver', { ... });
```

It calls `buildApp` directly, which is why `buildApp` is separate from `bin/`. `Template.fromStack` then synthesizes that one stack in memory. So the tests exercise Steps 3 to 6 exactly as the CLI would, and then assert on the JSON. They run in seconds, need no AWS credentials, and catch things like:

- a wrong policy ARN string;
- a missing option setting;
- an `ImportValue` sneaking into the Web stack.

They can't catch problems that only exist at deploy time. Examples:

- whether the managed policy at that ARN really exists (this session's bug);
- whether AppSync accepts a resolver's code;
- whether an SSM parameter is present.

---

## Try it yourself

All of these are safe: they synthesize or read, and never change AWS.

```bash
cd infra

# Steps 1-4: which stacks would this command touch?
npx cdk ls -c env=dev -c branch=$(git branch --show-current)

# Steps 1-6 into a throwaway directory; then poke around
npx cdk synth --all -c env=f-demo -c branch=try/it -c backend=provision -o /tmp/cdkout > /dev/null
ls /tmp/cdkout
python3 -m json.tool /tmp/cdkout/manifest.json | less           # find "dependencies"
grep -o '"Fn::ImportValue": "[^"]*"' /tmp/cdkout/*Api.template.json | head
grep -c ImportValue /tmp/cdkout/DlpAccessNext-Web-try-it.template.json   # 0: attaches by name
ls -A /tmp/cdkout/asset.*/ | head -40                            # what gets uploaded

# Step 7's change set, without executing it (needs AWS credentials)
npx cdk diff -c env=dev -c branch=$(git branch --show-current)

# Watch the validation in Step 4 fire
npx cdk ls -c env=Dev
npx cdk ls -c env=dev -c backend=provision
```

Experiments that teach well:

1. Change `SMALL_WEB.instanceType` in `infra/lib/environments.ts`, then run `cdk diff` against a deployed Web stack. You'll see a single option-setting change.
2. Edit a file under `src/`, synth twice (before and after), and compare the `S3Key` of the `Version` resource. The asset hash moves.
3. Temporarily comment out `web.addStackDependency(api)` in `infra/lib/app.ts` and synth in provision mode. The Web stack's manifest dependencies lose `…-Api`.

## Glossary

| Term | Meaning here |
| --- | --- |
| **App** | Root construct; one per `cdk` command run (`bin/appsync.ts`). |
| **Stack** | A construct that becomes one CloudFormation stack and template. |
| **Construct / L1 / L2** | A node in the tree. L1 = a raw `Cfn*` resource; L2 = a higher-level wrapper with defaults and `grant*` helpers. |
| **Context** | The key/value bag from `cdk.json` plus `-c` flags, read with `tryGetContext`. |
| **Synth** | Running your app to produce `cdk.out`. No AWS calls. |
| **Token** | A placeholder for a value known only at deploy time; becomes `Ref`, `Fn::GetAtt` or `Fn::ImportValue`. |
| **Asset** | A local file or directory CDK uploads to the bootstrap bucket, keyed by content hash. |
| **Bootstrap** | The one-time `cdk bootstrap` stack per account and region: asset bucket plus deploy roles (`hnb659fds`). |
| **Export / ImportValue** | CloudFormation's cross-stack wiring, generated automatically when a token crosses stacks; blocks deletion while in use. |
| **SSM-typed parameter** | `AWS::SSM::Parameter::Value<String>`; CloudFormation reads the named parameter at each deploy. Used for Web → Api. |
| **Service role vs instance role** | The service role is what Beanstalk acts as; the instance role (`dlp-access-next-<env>-eb`) is what the Next.js app acts as. |
| **Custom resource** | A Lambda that CloudFormation calls on create, update and delete, for things CloudFormation can't configure natively (the index template). |
