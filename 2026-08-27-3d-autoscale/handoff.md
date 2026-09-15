# Hand-off: 3D model auto-scale, camera framing, and ground sizing

**Repo:** `dlp-access` (branch `whunter-enhancement-3d-autoscale`)

## Current state

Four files modified, **not committed**:
- `src/components/Babylon/BabylonController.jsx`
- `src/components/Babylon/elements/Camera.tsx`
- `src/components/Babylon/elements/Ground.tsx`
- `src/components/Babylon/elements/Subject.tsx`

Behavior now:
- Models auto-frame to 60% of the camera's vertical FOV via camera distance (not mesh scaling). `Subject`'s old `scaleFactor` param is now an optional `cameraDistance` override.
- Camera zoom is clamped: can't dolly inside the model (`modelBoundingRadius * 1.2`), can't pull back more than `1.5x` the framing distance.
- Model always rests on the ground plane regardless of its own pivot; camera orbit target follows the model's true vertical center.
- Ground disc is sized at `upperRadiusLimit * 3` so its edge is never visible in frame at any zoom level (verified at both zoom extremes on two different models).

## Not yet done

- **No commit made.**
- `scaleFactor`/`scale_factor` config plumbing in `ArchivePage.js` and `ThreeD2DiiifHandler.tsx` was deliberately left untouched — it still reads per-item values from IIIF manifests but they're no longer passed into `Subject`/`Camera` at all (see summary.md for why). If per-item camera-distance overrides are wanted later, that's the place to wire it back in — pass the manifest's `scale_factor` value through to `Subject`'s `cameraDistance` constructor param instead of the current `null`.
- The known bug that `Subject`'s `modelDimensions`/`modelMaxSize` fields are derived from `model.ellipsoid` (a Babylon collision-shape default, not real geometry) was noticed but left alone — out of scope for this task, and nothing currently visible depends on it being correct.
- Constants worth knowing they're tunable, if the look needs adjusting further:
  - `TARGET_HEIGHT_RATIO = 0.6` (Subject.tsx) — how much of view-height the model fills
  - `MIN_RADIUS_MARGIN = 1.2`, `MAX_RADIUS_MULTIPLIER = 1.5` (Subject.tsx) — zoom clamp
  - `GROUND_RADIUS_MARGIN = 3` (Subject.tsx) — ground disc size relative to max camera distance
  - `DEFAULT_CAMERA_FOV = 0.8` (Subject.tsx) — must match Camera.tsx's (unset, so Babylon default) fov if that's ever changed explicitly

## Next steps

1. Test in the actual browser yourself across a wider variety of models/items than the two used this session (very flat/wide models, models with off-center pivots, etc.) — everything was verified against just a tall sculpture and a small flat button.
2. Decide whether to commit as one change or split by concern (camera framing / zoom limits / ground fix / ground sizing were each separate asks in this session, so history could go either way).
3. If satisfied, commit and open a PR — nothing has been pushed.
