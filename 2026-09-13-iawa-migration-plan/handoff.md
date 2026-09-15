# Handoff — iawa-migration-plan

## Context
Building on the prior `iawa-migration` session (which investigated
`Ms1990_007_Leviseur` and found leftover duplicate `FolderN/` directories),
this session covers a broader, related task: all 11 IAWA collections need
their "item" directories flattened to the collection root, removing
legacy sub-collection nesting (Box/Folder/etc). See `session-summary.md`
for the full investigation writeup and discovery results.

**S3 state has changed for one collection.** The user ran `migrate` live
on `Ms1990_025_Rudoff` (see "Current state of Rudoff" below); every other
collection has only been touched by read-only `discover` runs.

## Where the tool lives
`~/dev/dlp/ingest/vtdlp-aws-tools/go/migrate-tool/` — a Go module
(`iawa-migrate`), built and tested against real production S3 data
(read-only) as of this session. (Originally scaffolded at
`~/dev/dlp/assets/iawa/meta/migrate-tool/`; the user relocated it into the
shared `vtdlp-aws-tools` repo alongside this session's other tooling.)
Requires Go 1.21+ (built/tested with Go 1.24.2) and AWS
credentials with read/write access to
`vtdlp-pprd.img.cloud.lib.vt.edu` (this session used env-var credentials
already present in the shell — `aws sts get-caller-identity` confirmed
access as `vtdlp-whunter-workload`).

## How it works

**Discovery is structural, not name-based.** A directory is classified as
an "item" if it directly contains `manifest.json`; anything else
(recursively) is treated as a sub-collection to descend into. This was a
deliberate choice — sub-collection directories in this bucket are *not*
consistently named "Box"/"Folder" (counterexamples found:
`Ms1992_028_RolledDrawings`, `MapCap13`, `Drawer3`), and nesting depth
varies from 1–3 levels.

For each item found nested below the collection root, the tool builds:
- **Files**: every object under the item's own directory (`manifest.json`,
  `canvas/*.json`, `annotation/*.json`, `sequence/*.json`) — moved to
  `<CollectionRoot>/<ItemName>/...`, with `.json` files rewritten in
  transit (see below).
- **TileFiles**: every object under `<item's parent dir>/tiles/<ItemName>-<page>/...`
  (the tile pyramid for that item, which lives as a sibling of the item
  dir at whatever nesting level it's currently at) — moved to
  `<CollectionRoot>/tiles/<ItemName>-<page>/...` via a server-side S3
  `CopyObject` (no download needed for these binary tile images).

**URL rewriting** (per user decision this session — see
`session-summary.md`): every `.json` file being moved has its content
downloaded, and every occurrence of the old sub-collection path segment
(e.g. `Ms1990_025_Rudoff/Ms1990_025_Box1/Ms1990_025_Box1_Folder2/`) is
string-replaced with just the collection root
(`Ms1990_025_Rudoff/`), then re-uploaded to the new key. This fixes the
embedded `@id`/`service`/`thumbnail` URLs so they point at the item's new
location instead of the old, soon-to-be-deleted path — unlike the two
collections that were migrated in a prior, undocumented process
(`Pfeiffer`, `Leviseur`), which left those URLs stale.

**Concurrency**: a bounded pool of goroutines (`-concurrency`, default 16)
pulls file-move tasks off a channel and executes them in parallel — either
a server-side copy (tiles) or a download→rewrite→upload (JSON). Deletion
of old objects (only when `-delete` is passed) happens per-item, and only
after every one of that item's new objects has been written successfully
— so a partial failure never leaves an item's old copy deleted without a
complete new copy in place.

**Re-running after a partial migration (fixed this session)**: if an item
was already copied to root by a prior `migrate` run (no `-delete`), its
stale nested copy is now classified as `ItemMove.AlreadyAtRoot = true` —
a cleanup-only entry with no copy/rewrite step, safe for `-delete` to
remove. Discovery gets there by running two passes: first cataloging every
item already at the collection root, then checking each nested item's
file/tile-suffix set against the matching root item's. A match means
"already migrated, delete the stale copy"; a mismatch (same item name,
different files) still raises a blocking warning rather than silently
deleting something that turns out not to actually be a duplicate. A real
collision — two different nested sub-collections both wanting to claim the
same new root name, with neither already migrated — still blocks as a
warning too, unchanged from before. Before this fix, any name match
between a root item and a nested item was treated as a collision no
matter what, which made `-delete` impossible to ever run cleanly on a
collection that had been migrated in two passes (copy, then later
delete) — exactly the workflow this tool's own docs recommended.

## Build & run instructions

```bash
cd ~/dev/dlp/ingest/vtdlp-aws-tools/go/migrate-tool

# Build a binary (optional — `go run .` also works for one-off invocations)
go build -o iawa-migrate .
```

### `discover` — read-only, inspect what would move
```bash
./iawa-migrate discover -collection Ms1990_025_Rudoff
# or: go run . discover -collection Ms1990_025_Rudoff

# Flags:
#   -collection NAME   required, e.g. Ms1990_025_Rudoff
#   -bucket NAME       defaults to vtdlp-pprd.img.cloud.lib.vt.edu
```
Prints every item that would move (old path, new path, file/tile-file
counts) and any warnings (name collisions at the target root, or an item
whose tile pyramid couldn't be matched). **Zero warnings were found across
all 11 collections** during this session's investigation.

### `migrate` — do the move
```bash
# ALWAYS dry-run first:
./iawa-migrate migrate -collection Ms1991_025_Bliznakov -dry-run

# Then run for real (copies + rewrites; leaves old objects in place):
./iawa-migrate migrate -collection Ms1991_025_Bliznakov

# Spot-check the result in S3 (see "Suggested verification" below), then
# clean up the old objects once satisfied:
./iawa-migrate migrate -collection Ms1991_025_Bliznakov -delete

# Flags:
#   -collection NAME    required
#   -bucket NAME        defaults to vtdlp-pprd.img.cloud.lib.vt.edu
#   -concurrency N      default 16 — number of worker goroutines
#   -dry-run            log every planned action, write nothing to S3
#   -delete             after a successful copy, delete the item's old
#                       objects (per-item; skipped for any item that had
#                       a copy/rewrite failure)
```
`migrate` refuses to run live (non-dry-run) if `discover` surfaces any
warnings for that collection — resolve them first, or pass `-dry-run` to
preview anyway.

Note: `-delete` can be passed on the very first live run if you're
confident, but the safer path is: dry-run → live run without `-delete` →
spot-check → re-run the same command with `-delete` added. Re-running
`migrate` (no `-delete`) after objects already exist at the new location
is safe but not a no-op copy-wise: items already at root are now detected
as `AlreadyAtRoot` and skip copy/rewrite entirely (see "Re-running after a
partial migration" above) — the second run's job is just to report them
as cleanup-only and, if `-delete` is passed, remove the stale nested
copies.

### `verify` — confirm a collection is fully flattened
```bash
./iawa-migrate verify -collection Ms1991_025_Bliznakov
```
Re-runs discovery; prints `OK: <collection> has no nested items remaining`
and exits 0 if there's nothing left to move, otherwise prints the
remaining plan and exits 1.

## Current state of Rudoff (needs finishing)
The user's live trial run already happened on `Ms1990_025_Rudoff` (not
Bliznakov as originally suggested): `migrate -collection Ms1990_025_Rudoff`
(no `-delete`) ran for real and successfully copied all 54 items to the
collection root with rewritten URLs. The old nested copies (under
`Ms1990_025_Folder1/`, `Ms1990_025_Folder2/`,
`Ms1990_025_Box1/Ms1990_025_Box1_Folder2/`, and
`Ms1990_025_Box1/Ms1990_025_Box1_Folder3/`) are still on S3, unmodified.
With this session's fix, `discover -collection Ms1990_025_Rudoff` now
correctly shows all 54 as `[already at root - cleanup only]` with zero
warnings.

**Next action: spot-check, then finish Rudoff's cleanup.**
1. Manually inspect one or two of the already-migrated root items'
   `manifest.json` in S3 to confirm the rewritten URLs look correct (no
   remaining `Folder`/`Box` path segments).
2. `./iawa-migrate migrate -collection Ms1990_025_Rudoff -delete` — this
   will find nothing to copy (already done) and delete the 54 stale nested
   copies.
3. `./iawa-migrate verify -collection Ms1990_025_Rudoff` — should report
   `OK`.
4. The emptied sub-collection dirs (`Ms1990_025_Folder1/`, etc.) will still
   have their own leftover `collection/`, now-empty `tiles/`, and per-folder
   CSV — see "Known limitations" below, this isn't automated yet.

## Recommended next steps
1. Finish Rudoff (above) first, since it's already mid-flight.
2. Then work through the remaining, fully-legacy collections in ascending
   order of risk/size: Bliznakov (1 item — good next low-risk trial of the
   full dry-run → live → spot-check → `-delete` flow from a clean start) →
   Piomelli (55) → Zimbler (87) → Crawford (128) → Gottlieb (107,
   exercises the deepest/most irregular nesting) → Rodeck (501) →
   Chadeayne (451, largest object count, ~400K objects — expect this run
   to take the longest).
3. `Ms2005_002_Treder` has no image content to migrate — investigate
   separately why it's empty before assuming it's done.
4. `Ms1990_007_Leviseur`'s leftover duplicate `Ms1990_007_FolderN/`
   directories (documented in the prior `2026-09-13-iawa-migration`
   session) are a separate cleanup — not handled by this tool, since those
   are full duplicates of already-root-level items rather than nested
   originals.
5. Given the finding that `img.cloud.lib.vt.edu` (production CDN) appears
   to be backed by a **different bucket** than this `pprd` one, confirm
   with whoever owns the infrastructure whether/when `pprd` changes need
   to be promoted to production, and whether that promotion process
   itself needs the URL-rewrite this tool now does.

## Known limitations / things not yet built
- No automated update to `collection/top.json` manifests-list entries
  (root-level or per-sub-collection) — inspection this session showed
  these are already inconsistent/incomplete in production (e.g. Rudoff's
  root `collection/top.json` lists only 1 manifest despite ~8 root items
  existing), suggesting they may not be load-bearing, but this wasn't
  confirmed. Worth asking before assuming they can be ignored.
- No dedicated handling for the per-sub-collection CSV files (e.g.
  `Ms1990_057_Folder1.csv`) or emptied sub-collection prefix cleanup after
  a successful `-delete` — currently the sub-collection directory's own
  `collection/`, emptied `tiles/`, and CSV are left behind and would need
  a separate small cleanup pass (or a manual `aws s3 rm --recursive`) once
  a collection is fully verified.
- No automated tests were written for `buildPlan`'s classification logic
  (including the two-pass `AlreadyAtRoot` handling added this session); it
  was validated by manual review against `aws s3 ls` output for Rudoff and
  Gottlieb, the full 11-collection read-only discovery run producing zero
  warnings, and re-running `discover`/`migrate -dry-run -delete` against
  Rudoff's real, partially-migrated state after the fix. A unit test
  suite around `buildPlan` (using the `s3Lister`/`s3RW` interfaces with a
  fake in-memory key set) would be worth adding before running this
  against the larger collections, given how much production data hinges
  on this logic staying correct as more edge cases surface.
