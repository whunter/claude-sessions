# Session: 3D model auto-scale, camera framing, and ground sizing

**Date:** 2026-08-27
**Repo:** `dlp-access` (branch `whunter-enhancement-3d-autoscale`)
**Goal:** Make the Babylon.js 3D model viewer automatically frame any glTF/glb model at a consistent height, using camera positioning rather than model scaling, and fix the ground plane so it looks right at every zoom level.

## Background

`Subject.tsx` previously scaled every loaded model by a `scaleFactor` prop (default `0.25`, or per-item `scale_factor` from IIIF manifest config), a value hand-tuned per archive item. The task was to instead auto-frame the model at 60% of the camera's view height — first attempted via model scaling, then switched (per user direction) to camera positioning, since that preserves the model's real-world dimensions.

Two live local test items were used throughout:
- `http://localhost:3000/archive/4339dbe9` — a tall wood sculpture (`48 x 36 x 180 in`)
- `http://localhost:3000/archive/b3f2eed1` — a small flat button (`model/glb`)

## What changed, in order

1. **Camera-based auto-framing** (`Subject.tsx`, `Camera.tsx`, `BabylonController.jsx`)
   - `Subject`'s 3rd constructor param changed from `scaleFactor` (mesh multiplier) to an optional `cameraDistance` override.
   - Added `getCameraDistance()`: computes the distance needed for the model's real height to fill 60% of the camera's vertical FOV, using `getHierarchyBoundingVectors` for true bounding dimensions (previously `model.ellipsoid` was used for "dimensions," which is actually a Babylon collision-ellipsoid default, not real geometry — left as-is, out of scope).
   - `BabylonController.jsx` now awaits `Subject.ready` before constructing the `Camera`, then passes `getCameraDistance()` as the initial radius.
   - **Decision**: left `scaleFactor` config plumbing (`ArchivePage.js`, `ThreeD2DiiifHandler.tsx`) untouched — those still read `scale_factor` from IIIF manifests but the value is no longer wired into `Subject`, since repurposing it as a camera distance would silently break every item with a manifest-tuned scale value. This was an explicit user call after being flagged.

2. **Zoom limits** (`getCameraRadiusLimits()` in `Subject.tsx`, applied in `Camera.tsx`)
   - Lower limit: `modelBoundingRadius * 1.2` — camera can't dolly inside the model.
   - Upper limit: `distance * MAX_RADIUS_MULTIPLIER` (currently `1.5`, tuned down from an initial `3` after user feedback it allowed the camera too far away).

3. **Ground clipping fix** (`Subject.tsx`)
   - Bug: model was positioned at exact origin regardless of its own pivot, so unscaled real-world models could clip through the ground disc (fixed at `y = -1`).
   - Fix: model is now positioned so its bounding-box minimum Y rests exactly on `GROUND_Y = -1`, and the camera's orbit target (`getCameraTarget()`) is now the model's true vertical center (not a fixed origin), so framing stays correct after the repositioning.

4. **Ground sizing/scaling — three iterations, ending with a fixed formula**
   - v1: dynamically rescaled the ground mesh every frame (`Ground.setScale`, driven by `camera.radius / referenceRadius`) so its *apparent* size stayed constant across zoom. Removed later.
   - v2: sized the ground as a fixed world radius so the *entire* disc would be visible within frame at max zoom-out (using vertical-FOV geometry accounting for the camera's fixed height above the ground plane). Worked, but visually looked like a hard-clipped "horizon line" as the camera's downward viewing angle to the ground got shallower with zoom.
   - **v3 (final)**: ground radius = `upperRadiusLimit * 3` (`GROUND_RADIUS_MARGIN = 3`). Reasoning: for a circle of radius `R`, any point on it is at least `R - D` from a camera at distance `D` from center — so making `R` several times larger than the camera's max possible distance guarantees the camera always stays deep inside the disc's footprint, so its edge/boundary is never visible in frame, at any zoom level. `Ground.setScale` (from v1) was removed as dead code.

## Verification

Typechecked (`tsc --noEmit`) clean after every change. Visually verified in Chrome against both test items at multiple points:
- Default view: both models auto-frame correctly, ground visible below without clipping.
- Because the browser automation's mouse-wheel zoom was unreliable in this environment (kept bubbling to page scroll instead of the Babylon canvas), used a webpack-internal trick to grab the live `EngineStore`/scene/camera directly from the page and force `camera.radius` to `lowerRadiusLimit`/`upperRadiusLimit` for exact, repeatable checks:
  ```js
  let req;
  window.webpackChunkitem_display.push([[Symbol()], {}, (r) => { req = r; }]);
  const EngineStore = req.c['./node_modules/@babylonjs/core/Engines/engineStore.js'].exports.EngineStore;
  const camera = EngineStore.Instances[0].scenes[0].activeCamera;
  ```
- Confirmed at both zoom extremes, on both items: no ground edge visible, no console errors.

## Final file states (uncommitted)

- `src/components/Babylon/BabylonController.jsx`
- `src/components/Babylon/elements/Camera.tsx`
- `src/components/Babylon/elements/Ground.tsx`
- `src/components/Babylon/elements/Subject.tsx`

No commit was made — not requested during the session.
