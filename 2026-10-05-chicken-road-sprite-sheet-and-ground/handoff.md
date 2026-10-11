# Handoff — Chicken Road (Unity)

## Current state

Everything is committed and pushed: `main` at `0519369` on
https://github.com/whunter/chicken-game.git. Working tree clean. The latest build
is in `Build\ChickenRoad.exe` and was running when the session ended.

```
C:\Users\wleeh\UnityProjects\ChickenRoad   (WSL: ~/chicken-road symlink)
├── Assets/Editor/SceneBuilder.cs     # generates the whole scene — edit this, not the .unity file
├── Assets/Editor/PlayerBuilder.cs    # Windows player build
├── Assets/Scripts/ChickenController.cs  # moveSpeed 9, runFrameRate 52.73, flipX = input > 0
├── Assets/Scripts/GameManager.cs     # win when chicken bounds.min.x >= finishLineX (3)
├── Assets/Scripts/CameraFollow.cs, WindowSetup.cs
└── Assets/Sprites/chicken_run_2_smooth_12frame_sheet.png  # EDITED in place (original in 8909a63)
```

## How to build and run (from WSL)

```
powershell.exe -NoProfile -Command '$p="C:\Users\wleeh\UnityProjects\ChickenRoad"; $u="C:\Program Files\Unity\Hub\Editor\6000.6.3f1\Editor\Unity.exe"; Get-Process ChickenRoad -ErrorAction SilentlyContinue | Stop-Process; $r=Start-Process $u -ArgumentList "-batchmode -nographics -quit -projectPath `"$p`" -executeMethod SceneBuilder.BuildScene -logFile `"$p\scene.log`"" -Wait -PassThru; "scene exit " + $r.ExitCode; $r=Start-Process $u -ArgumentList "-batchmode -nographics -quit -projectPath `"$p`" -executeMethod PlayerBuilder.BuildWindows -logFile `"$p\build.log`"" -Wait -PassThru; "build exit " + $r.ExitCode; Start-Process "$p\Build\ChickenRoad.exe"'
```

Then check `scene.log` for `BuildScene completed successfully` and `build.log` for
`Build Finished, Result: Success` (grep also for `error CS|Exception`).
The Unity editor must not have the project open during batchmode builds.

## Key facts to know before changing things

- **Scene geometry (SceneBuilder constants):** ground is `GroundRows = 2` tile rows
  from `GroundBottom = -5` to `GroundTop = -1`; tiles are 128px at 64 PPU
  (`TileWorldSize = 2`). Road half-width 3 at the bottom, tapering
  `RoadTaperPerUnit = 0.5` per unit height (half-width 1 at top). Level x −11..11.
  Camera orthographic size 5, background sky color, follows chicken in x only.
- **Chicken:** feet at `ChickenGroundY` = −3.625 (bottom row top − 25% of a 590px
  frame height). Sprites face LEFT, so `flipX = true` means facing right.
  Run sequence = 12 frames with frame 0 (extended) repeated `ChickenExtendedHold = 10` times.
  Pivot is at the feet; all frames share the same crop/pivot.
- **Serialized defaults:** `runFrameRate` comes from the script default at AddComponent
  time (rebuilding the scene picks up changes); `moveSpeed` is set explicitly in SceneBuilder.
- **Sprite sheet bounce is baked into the PNG.** The editing script (`raise.py`) was in
  a session scratchpad and is gone; the original sheet is in commit `8909a63` if a redo
  is needed. Per-frame lift was `[30,28,22,14,8,2,0,2,8,14,22,28]` px with the shadow
  fixed; feet distinguished from shadow by orange color (R−B > 40) in rows ≥ 580.
- **Lane line** is its own 24-slice strip mesh (`CreateLaneLineMesh`) that narrows
  with the road; dash length is constant in world y (not perspective-shortened).
- **Tiles** are generated in code (`CreateGrassTexture` solid green, `CreateRoadTexture`
  with soft specks, `CreateLaneLineTexture` rounded dashes centred on the u=0 seam).
- **Finish line** is invisible; win check still at x = 3 (road's far bottom edge).
- **Git:** `core.autocrlf false`, `core.fileMode false`, LF enforced via
  `.gitattributes`; no git-lfs installed. Commit after each turn; ask before pushing.
- **Don't** take desktop screenshots to verify visuals — that captured the user's
  desktop instead of the game. Verify textures by rendering previews with PIL instead.

## Possible next steps (none requested yet)

- Perspective-shorten lane dashes toward the top of the road.
- The grass/road diagonal mesh edges rely on 2× MSAA from the Ultra quality level;
  raise it if they look jagged.
- Decide whether the win condition should move now that the finish line is invisible.
