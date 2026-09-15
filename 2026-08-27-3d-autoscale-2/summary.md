# Session: 3D model auto-scale, part 2 — ground clipping and camera near-plane fixes

**Date:** 2026-08-27
**Repo:** `dlp-access` (branch `whunter-enhancement-3d-autoscale`)
**Previous session:** [2026-08-27-3d-autoscale](../2026-08-27-3d-autoscale/) — implemented camera-based auto-framing, zoom limits, the ground-clipping-through-model fix, and ground sizing (v1→v2→v3, ending on `upperRadiusLimit * 3`). That session ended with everything uncommitted.

**Goal:** Pick up the uncommitted work from the previous session, fix reported visual bugs in the ground/camera far- and near-clip behavior, and get the result committed.

## What happened, in order

1. **Verified hand-off state matched.** Confirmed the working tree exactly matched the previous session's hand-off doc (4 modified files, same diff stat) before making changes.

2. **"Ground looks rectangular" bug — first attempt (reverted).**
   - Diagnosed as `camera.maxZ` (Babylon default 10000) being smaller than the ground disc's radius for large models, so the far clip plane truncated the disc with a straight cut instead of its round edge.
   - Added `Subject.getCameraMaxZ()` and wired a `maxZ` param through `Camera.tsx` → `BabylonController.jsx`.
   - **Regression found**: for *small*-scale models, this formula shrank `maxZ` down to ~1 unit — far below what's needed to render `Environment.tsx`'s fixed size-100 skybox box. The far plane sliced through the skybox itself, which (being a box) showed up as a hard square edge when looking down. Patched to floor `maxZ` at a 10000 baseline.
   - **User reported still clipping, worse when looking down** — asked to revert entirely rather than keep chasing it. All `maxZ`-related changes were reverted from `Camera.tsx`, `Subject.tsx`, and `BabylonController.jsx`, back to the original hand-off state (Babylon's default `maxZ`).

3. **User asked to revert ground sizing further, to before the hand-off session's v3 approach.** Offered a choice (discard everything / v2 / v1); user picked **v1**: dynamic per-frame rescaling.
   - Rewrote `Ground.tsx` to store a `referenceRadius` and expose `setScale(cameraRadius)`, which uniformly rescales the mesh by `cameraRadius / referenceRadius` so the disc's *apparent* on-screen size stays roughly constant as the camera zooms.
   - `Subject.tsx`: removed `getGroundRadius()`/`GROUND_RADIUS_MARGIN` (no longer needed).
   - `BabylonController.jsx`: ground now constructed at `model.getCameraDistance()` (the framing distance, used as the scale-1 reference); added a `scene.onBeforeRenderObservable` callback calling `ground.setScale(camera.radius)` every frame.
   - Verified in-browser: ground's curved bottom edge visible at max zoom-out, shrinks at max zoom-in — matches the v1 behavior the user wanted.

4. **Committed.** First commit (`0c1e2a1`): the full auto-framing feature from the previous session plus the v1 ground-rescaling redo, as a single commit ("Auto-frame 3D models via camera distance instead of mesh scaling").

5. **Ground diameter tweak.** User asked to decrease the ground disc's diameter by 5%. Added `DIAMETER_SCALE` constant in `Ground.tsx`, applied to the incoming radius before mesh creation and before it's stored as the rescale reference (so the 5% reduction persists correctly through the dynamic per-frame rescaling). Not committed at this point — left pending.
   - (User later independently edited `DIAMETER_SCALE` to `0.75` directly in the file, outside this session's tool calls — noted but not reverted, per the harness's out-of-band-edit convention.)

6. **"Camera clips inside the object when zoomed all the way in" — the real near-plane bug.**
   - Mid-investigation, user separately reported changing `DEFAULT_LOWER_RADIUS_LIMIT` in `Camera.tsx` "but it didn't work" — explained that constant is only a fallback for callers that don't pass an explicit `lowerRadiusLimit` (i.e., the commented-out `UniversalCamera` path); `BabylonController.jsx` always passes an explicit value computed by `Subject.getCameraRadiusLimits()`, so editing the Camera.tsx default has no effect. The actual knob is `MIN_RADIUS_MARGIN` in `Subject.tsx`.
   - Root cause of the clipping: `camera.minZ` was hardcoded to `0.1` in `Camera.tsx`, independent of model scale. For a small-scale model (the sculpture test item, scene units ~0.03–0.1), `0.1` was *larger* than the camera's own `lowerRadiusLimit` (~0.077) — so at max zoom-in the entire model fell inside the near-clip region and was culled outright. Confirmed via direct camera introspection in the browser (webpack-internal `EngineStore` trick from the previous session) — screenshots at `radius = lowerRadiusLimit` showed a black/empty frame, not the model.
   - Fixed by adding `Subject.getCameraMinZ()`: computes `minZ` as a fraction (`MIN_Z_MARGIN = 0.5`) of the gap between `lowerRadiusLimit` and `modelBoundingRadius`, so it's always safely inside whatever range the camera can reach, regardless of model scale. Wired through `Camera.tsx` (new `minZ` constructor param, default `0.1` preserved for the unused `UniversalCamera` fallback path) and `BabylonController.jsx`.
   - **Also fixed a related latent bug found while investigating**: `Subject.tsx`'s model-centering only ever adjusted the model's Y position (to rest it on the ground); X/Z were left at the mesh's original, possibly off-center pivot. This meant the camera's orbit target `(0, y, 0)` and the model's true bounding-box center could disagree, so `modelBoundingRadius`'s enclosing sphere didn't actually bound the model from every direction — the near-zoom clamp could under-protect at some azimuth angles even before the minZ bug. Now recenters the model on its true X/Z bounding-box center.
   - Verified in-browser: at `radius = lowerRadiusLimit`, from multiple azimuth angles, on both test items — model renders fully in detail, no clipping.

6. **Committed** in two separate commits:
   - `b89f382` — the minZ fix + model-recentering fix (`Camera.tsx`, `Subject.tsx`, `BabylonController.jsx`, and — per lint-staged/prettier — a formatting pass touched `Ground.tsx` too).
   - `bf66945` — a one-line, unrelated change the user had made directly to `Environment.tsx` (skybox `size: 100` → `1000`), committed separately at the user's request rather than folded into the clipping-fix commit.

## Final state

Branch `whunter-enhancement-3d-autoscale`, 3 commits ahead of the merge base, working tree clean, nothing pushed:
```
bf66945 Increase skybox size to 1000
b89f382 Prevent camera near-clip plane from culling small-scale models at max zoom
0c1e2a1 Auto-frame 3D models via camera distance instead of mesh scaling
```

Ground sizing is now **v1** (dynamic per-frame rescale to a reference distance, minus 25% diameter per the user's last direct edit to `DIAMETER_SCALE`), not the v3 approach the original session ended on. The far-clip (`maxZ`) experiment from earlier in this session was fully reverted and never committed — Babylon's default `maxZ` (10000) is what's live.

Verification throughout was done live in Chrome against the same two test items as the previous session (`/archive/4339dbe9` — tall sculpture, `/archive/b3f2eed1` — small button), using the same webpack-internal `EngineStore` trick to grab the live camera/scene for exact, repeatable radius/angle checks, since mouse-wheel zoom doesn't reliably reach the Babylon canvas in the browser-automation environment.

## Not yet done

- Nothing pushed to remote.
- The `DIAMETER_SCALE = 0.75` value in `Ground.tsx` was set by the user directly (not through a request in this session) — worth confirming that's the final intended value before merging.
- No further model variety was tested beyond the same two items used across both sessions (tall sculpture, small flat button) — the original hand-off's suggestion to test flat/wide models and off-center-pivot models more broadly still stands, especially now that centering logic has changed.
