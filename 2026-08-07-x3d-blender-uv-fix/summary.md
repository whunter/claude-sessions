# Session: Scrambled texture on X3D butterfly model in Blender

**Date:** 2026-08-07
**Directory:** `/Users/whunter/dev/dlp/assets/vtec/media/glb_tests`
**Goal:** Diagnose why `VTEC000000374.x3d` (a photogrammetry-scanned butterfly specimen) rendered correctly in x3dom (browser) but showed a scrambled/torn texture when imported into Blender.

## Starting point

Two reference screenshots: `x3dom` render (correct) vs. Blender render (scrambled), plus the `.x3d` model and a texture PNG in the working directory.

## Investigation

Worked through several layered issues, verifying each empirically rather than guessing:

1. **Missing texture file.** The `.x3d`'s `<ImageTexture url ="LowRes_VTEC000000374_X3D.png"/>` referenced a file that didn't exist in the directory — only an unrelated full-resolution reference photo (`VTEC000000374.png`) was present. User located and renamed the correct file in; also renamed the `.x3d` itself to `LowRes_VTEC000000374_X3D.x3d`.
2. **Invalid MFString quoting.** Even with the file present, Blender's `web3d_x3d_vrml2_format` extension (v2.5.1) failed to load it: the `url` attribute lacked the inner quotes required by strict X3D MFString XML encoding (`url ="file.png"` vs. the required `url='"file.png"'`). Browsers/x3dom are lenient about this; Blender's `mfstring.decode()` is strict and silently returned an empty URL list with only a console warning. User fixed the XML to `url='"LowRes_VTEC000000374_X3D.png"'`.
3. **Texture still scrambled after both fixes.** Traced this to a real bug in the Blender add-on's XML parser: for this file's `IndexedFaceSet`, the add-on's custom SAX wrapper (used for line-number tracking in error messages) silently drops the `TextureCoordinate` sibling element — almost certainly triggered by the ~1.9MB `coordIndex`/`texCoordIndex` attribute strings. With no `TextureCoordinate` found, the importer falls back to its own bounding-box-projected "generated" UVs.
   - Proved this concretely: reimplemented the importer's per-loop UV algorithm in plain Python against the raw XML and got healthy UV spread across the whole mesh; the actual Blender output, sampled the same way, matched the bounding-box **fallback formula** at 57/57 sampled points — not the real per-vertex UVs.
   - Confirmed the raw XML itself parses fine and is internally consistent (equal face counts/lengths between `coordIndex` and `texCoordIndex`, no malformed tokens) — the corruption is specifically in Blender's runtime parsing, not the source file.
   - Also separately confirmed (via headless renders) that a large flat blank rectangle visible in every render angle is a real geometric feature of the scan (the specimen's mounting/backing card), not a symptom of the bug — verified by rendering the mesh silhouette with no material at all.

## What was built

1. **`fix_uv.py`** (in the model's directory) — model-specific one-off fix: re-parses `coordIndex`/`texCoordIndex`/`TextureCoordinate` straight from the `.x3d` via regex and overwrites the active UV layer on the already-imported mesh, bypassing Blender's broken parser. Verified via headless Blender render (cropped before/after comparison): broken import showed a jagged mismatched-triangle mess; after the fix, a coherent wing pattern (fringe, brown base color, line of pale spots) matching the raw texture atlas.
2. **`fix_all_uv.py`** (in the model's directory) — generalized version for any `.x3d` file, at user request. Differences from `fix_uv.py`:
   - Real XML parsing (`xml.etree.ElementTree`) instead of regex.
   - Handles multiple `IndexedFaceSet` elements per file.
   - Resolves `DEF`/`USE` references for `TextureCoordinate`.
   - Handles `ccw="false"` by mirroring Blender's own loop-reversal.
   - Falls back to indexing texture coords via `coordIndex` when `texCoordIndex` is omitted (per X3D spec).
   - Transparently decompresses gzipped `.x3dz`.
   - Matches each Blender mesh object to the correct `IndexedFaceSet` block by polygon count (invariant to Blender's internal vertex culling), rather than assuming one hardcoded object.
   - Operates on selected mesh objects, or all mesh objects in the scene if none selected.
   - Skips anything unfixable with a printed reason; has a `DRY_RUN` flag.
   - Re-tested against the real file after generalizing — UV spread matched the known-good result exactly.
3. **`FIX_UV_README.md`** (in the model's directory) — usage instructions for `fix_uv.py`: prerequisites, step-by-step Blender workflow, and a note to file the underlying bug against the extension at `projects.blender.org/extensions/io_scene_x3d`.

## State at end of session

- Model directory now contains: `LowRes_VTEC000000374_X3D.x3d`, `LowRes_VTEC000000374_X3D.png`, `fix_uv.py`, `fix_all_uv.py`, `FIX_UV_README.md`.
- Fixes were verified via headless Blender renders during the session (not run inside the user's live GUI session) — user still needs to run `fix_uv.py` or `fix_all_uv.py` in their own Blender session after importing, and save/export the result, for the fix to take effect there.
- The `.x3d` file's UV data itself was never modified — the fix patches Blender's in-memory mesh only, so it must be re-run after every fresh import.
- Not filed upstream: recommended but not done, that the Blender extension bug (silently dropping sibling XML elements for `IndexedFaceSet` nodes with very large index attributes) be reported at `projects.blender.org/extensions/io_scene_x3d`.
