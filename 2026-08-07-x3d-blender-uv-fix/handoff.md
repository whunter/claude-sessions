# Hand-off: Scrambled texture on X3D butterfly model in Blender

**Directory:** `/Users/whunter/dev/dlp/assets/vtec/media/glb_tests`

## Current state

- Model directory contains: `LowRes_VTEC000000374_X3D.x3d`, `LowRes_VTEC000000374_X3D.png`, `fix_uv.py` (model-specific), `fix_all_uv.py` (generalized, any `.x3d`), `FIX_UV_README.md`.
- Root cause identified: Blender's `io_scene_x3d` extension (v2.5.1) silently drops the `TextureCoordinate` sibling element when parsing an `IndexedFaceSet` with very large `coordIndex`/`texCoordIndex` attribute strings (~1.9MB here), causing it to fall back to bounding-box-projected UVs instead of the real per-vertex UVs.
- Fixes verified via headless Blender renders during the session only — not yet run inside the user's interactive Blender GUI session.
- The `.x3d` file's UV data itself was never modified; the fix patches Blender's in-memory mesh after import, so it must be re-run every time the model is freshly imported.

## Not yet done

- User still needs to run `fix_uv.py` (this model) or `fix_all_uv.py` (general) inside their own Blender session after importing, then save/export the corrected result.
- Bug not yet filed upstream against `projects.blender.org/extensions/io_scene_x3d`.

## Next steps

1. In Blender, import the `.x3d`, then run `fix_all_uv.py` (or `fix_uv.py` for just this model) from the Scripting tab.
2. Save/export the mesh with corrected UVs so the fix persists without re-running the script.
3. If other X3D models in the `vtec` collection show the same scrambled-texture symptom, try `fix_all_uv.py` on them directly — it's designed to generalize (multiple `IndexedFaceSet`s, `DEF`/`USE`, `ccw="false"`, gzipped `.x3dz`).
4. Consider filing the upstream bug report so future Blender versions/extension releases fix this without the workaround script.
