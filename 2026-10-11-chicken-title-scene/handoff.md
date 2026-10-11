# Handoff — Chicken Game (Unity)

## Current state

`main` is at `c5a6f00` locally; `origin/main` (https://github.com/whunter/chicken-game.git)
is at `e09330d`, one commit behind (the unused-sprite cleanup). Working tree clean.
`Build/ChickenGame.exe` was rebuilt from `c5a6f00`.

```
C:\Users\wleeh\UnityProjects\ChickenGame   (WSL: ~/chicken-game symlink)
├── build.sh                              # ./build.sh: scene rebuild + Windows player build
├── Assets/Editor/SceneBuilder.cs         # generates the whole scene; edit this, not the .unity file
├── Assets/Editor/PlayerBuilder.cs        # Windows player build → Build/ChickenGame.exe
├── Assets/Scripts/ChickenController.cs   # run, slide, peck queue, turn in place, corn check
├── Assets/Scripts/CornPile.cs            # 5 states, Advance(), fixed halfWidth footprint
├── Assets/Scripts/GameManager.cs         # winTriggerEnabled = false for now
└── Assets/Sprites/corn_pile_sheet_{0,1,2}.png  # EDITED: baked shadow removed, oval added
```

## How to build (from WSL)

```
./build.sh
```

Close the Unity Editor first; batch mode can't open a project the Editor has open
(exit code 1, licensing noise in `scene.log`). If the Editor must stay open, scripts can
be compile-checked with Unity's bundled Roslyn
(`Editor/Data/DotNetSdk/dotnet.exe` + `DotNetSdk/sdk/8.0.318/Roslyn/bincore/csc.dll`,
using a response file because the paths contain spaces).

## Key facts to know before changing things

- **Sprites face left:** `flipX = true` means facing right.
- **Corn pile:** at x = 6, `ChickenGroundY`, sorting order 4. Pivot (260, 269) in each
  520×353 cell; PPU matches the chicken (531/2.25 ≈ 236). Only variant 0 is shown;
  `LoadCornPileSheets` still slices all three.
- **Corn check:** decided at the space press (near + facing), applied when that peck
  reaches its last (head-down) frame. Near = gap from chicken renderer bounds to the
  pile's ±`halfWidth` (0.79) footprint ≤ 0.5 × chicken bounds width.
- **Corn sheet edits are baked into the PNGs.** The script (`corn_shadow.py`) was in the
  session scratchpad and is gone. Originals are in git before `535856a`. Shadow style:
  RGB (93, 80, 68), alpha 129, 17px tall, matching the chicken's.
- **Stable scene IDs:** `MakeSceneFileIdsStable` renumbers the saved scene by hashing each
  object's hierarchy path + component type. Renaming or reordering objects changes their
  IDs, which is expected. A warning is logged if any object keeps a random ID.
- **Turn in place:** `turnHoldTime` 0.12s; applies from any standstill, not only turn-arounds.
- **Win trigger** at x = 3 is disabled because it fired before the chicken reached the corn.
- **Git:** commit after each turn; ask before pushing. No co-author lines in commits.

## Possible next steps

- Push `c5a6f00`.
- Give the win a new condition (e.g. finishing the corn, or reaching the right edge).
- Optionally limit the turn delay to turn-arounds only.
