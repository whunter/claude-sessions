# Hand-off: 3D model auto-scale, part 2 — ground clipping and camera near-plane fixes

**Repo:** `dlp-access` (branch `whunter-enhancement-3d-autoscale`)
**Previous session:** [2026-08-27-3d-autoscale](../2026-08-27-3d-autoscale/) — read that hand-off first; this session picked up exactly where it left off (same 4 uncommitted files) and diverged from there.

## Current state

Working tree is **clean**. 3 commits ahead of `66e7652` (the last commit before this feature work started), nothing pushed:
```
bf66945 Increase skybox size to 1000
b89f382 Prevent camera near-clip plane from culling small-scale models at max zoom
0c1e2a1 Auto-frame 3D models via camera distance instead of mesh scaling
```

## Behavior now (differs from the previous session's hand-off in two ways: ground sizing and near-clip)

- Models auto-frame to 60% of the camera's vertical FOV via camera distance (unchanged from previous session).
- Camera zoom is clamped: lower = `modelBoundingRadius * 1.2`, upper = `distance * 1.5` (unchanged).
- Model rests on the ground plane, **and is now also recentered on its true X/Z bounding-box center** (`Subject.tsx` `init()`) — not just repositioned vertically. This matters because the camera's orbit target assumes `(0, y, 0)`; if the model's mesh pivot wasn't already centered, the old code left a gap between the assumed and actual bounding-sphere center, which could let the camera get closer to the model's surface than `lowerRadiusLimit` intended from some angles.
- **Ground sizing is back to the "v1" dynamic-rescale approach**, not the v3 (`upperRadiusLimit * 3`, fixed-size, never-see-the-edge) approach the previous session ended on. `Ground.tsx` now has a `setScale(cameraRadius)` method; `BabylonController.jsx` calls it every frame via `scene.onBeforeRenderObservable`, rescaling the disc by `cameraRadius / referenceRadius` so its *apparent* screen size stays roughly constant across zoom — meaning the disc's curved edge **is** visible at max zoom-out, by design (this is what the user explicitly asked for after two other approaches were tried and reverted this session).
  - `Ground.tsx` also has `DIAMETER_SCALE = 0.75` applied to the incoming radius — this exact value (0.75, i.e. a 25% reduction) was set by the user editing the file directly mid-session, not through an explicit request I fulfilled. Worth double-checking this is the final intended value.
- **`camera.minZ` is no longer hardcoded to `0.1`.** `Subject.getCameraMinZ()` computes it as `(lowerRadiusLimit - modelBoundingRadius) * 0.5`, so it always sits safely inside the gap between the model's surface and the closest the camera is allowed to zoom, regardless of model scale. This fixes the actual bug reported this session: at max zoom-in on small-scale models, the old fixed `0.1` near-clip was larger than `lowerRadiusLimit`, so the whole model fell inside the near-clip region and was culled outright (looked exactly like the camera clipping into the object).
- `camera.maxZ` is back to Babylon's default (10000) — an experimental fix here (scaling `maxZ` to the ground radius, to solve a separately-reported "ground looks rectangular / square" bug) was tried, made things worse for small-scale models by clipping the skybox, and was fully reverted at the user's request. **This bug (ground edge looking rectangular/square under certain camera angles) is not fixed** — it was worked around by reverting ground sizing to v1 instead of solved directly. If it resurfaces, don't re-attempt the `maxZ`-scaling approach without also accounting for `Environment.tsx`'s fixed-size skybox (currently `size: 1000`, bumped up this session from `100`, unrelated to the clipping investigation — a user edit made directly and committed separately at their request).

## Key files

- `src/components/Babylon/BabylonController.jsx` — wires `Subject`/`Ground`/`Camera` together; owns the per-frame ground rescale callback.
- `src/components/Babylon/elements/Subject.tsx` — model loading, centering, all the camera-distance/radius-limit/minZ math. Constants: `TARGET_HEIGHT_RATIO=0.6`, `MIN_RADIUS_MARGIN=1.2`, `MAX_RADIUS_MULTIPLIER=1.5`, `MIN_Z_MARGIN=0.5`.
- `src/components/Babylon/elements/Camera.tsx` — thin wrapper; `lowerRadiusLimit`/`upperRadiusLimit`/`target`/`minZ` are all passed in from `Subject`, not computed here. The `DEFAULT_*` constants in this file are **only fallbacks for the unused, commented-out `UniversalCamera` path** — editing them has no effect on the live arc-rotate camera. (This tripped up the user mid-session; worth remembering.)
- `src/components/Babylon/elements/Ground.tsx` — `setScale(cameraRadius)` for the v1 dynamic rescale; `DIAMETER_SCALE` constant.
- `src/components/Babylon/elements/Environment.tsx` — skybox, now `size: 1000` (was `100`).

## Verification approach

No automated tests exist for this. All verification was manual, live in Chrome via `mcp__claude-in-chrome__*` tools, against two items also used in the previous session:
- `http://localhost:3000/archive/4339dbe9` — tall wood sculpture, small scene-unit scale (camera radius range ~0.077–0.27)
- `http://localhost:3000/archive/b3f2eed1` — small flat button, larger scene-unit scale (camera radius range ~8.9–29)

Mouse-wheel zoom doesn't reliably reach the Babylon canvas in this environment (scrolls the page instead), so radius/angle were set directly via a webpack-internal trick to grab the live camera object:
```js
let req;
window.webpackChunkitem_display.push([[Symbol()], {}, (r) => { req = r; }]);
const EngineStore = req.c['./node_modules/@babylonjs/core/Engines/engineStore.js'].exports.EngineStore;
const camera = EngineStore.Instances[0].scenes[0].activeCamera;
```
Then set `camera.radius`, `camera.alpha`, `camera.beta`, `camera.useAutoRotationBehavior = false` directly before screenshotting.

## Not yet done / next steps

1. **Confirm `DIAMETER_SCALE = 0.75` is intentional** — it was a direct file edit by the user, not something explicitly requested and confirmed in conversation.
2. **The "ground edge looks rectangular/square" bug was sidestepped, not fixed.** It only came up under the v2/v3 ground-sizing approaches (fixed large disc + far-clip interactions); since ground sizing is back to v1, it may simply not be reachable anymore — but this hasn't been explicitly re-tested since reverting to v1. If it's re-reported, the fix needs to jointly account for ground radius, `camera.maxZ`, and the skybox's fixed size, not just ground radius alone.
3. **Broader model testing still hasn't happened** — same two items used throughout both sessions. The recentering fix in `Subject.tsx` (X/Z as well as Y) specifically changes behavior for models with off-center pivots, which is exactly the case that was never tested before either session — worth prioritizing an off-center-pivot model if one is available.
4. Nothing has been pushed. Decide when to push / open a PR.
