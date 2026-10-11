# Session Summary — Chicken Game: Corn Pile, Turn in Place, Build Script

**Date:** 2026-10-11
**Project:** `C:\Users\wleeh\UnityProjects\ChickenGame` (WSL: `/mnt/c/Users/wleeh/UnityProjects/ChickenGame`, symlinked as `~/chicken-game`)
**Remote:** https://github.com/whunter/chicken-game.git (`main`, pushed through `e09330d`; `c5a6f00` committed locally, not pushed)

## Context

Chicken Game (renamed from Chicken Road) is a Unity 6000.6.3f1 2D side-scroller built
from WSL with the Windows Unity CLI in batch mode. `Assets/Editor/SceneBuilder.cs`
generates the whole scene; `PlayerBuilder.BuildWindows` builds `Build/ChickenGame.exe`.
The chicken runs left/right, slides to a stop, and pecks on space.

## What was done

### Corn pile (`fdfed64`, `2fd8700`)
1. Added `Assets/Scripts/CornPile.cs`: holds the 5 states of `corn_pile_sheet_0`
   (full pile → stray kernels), `Advance()` steps one state and stops at the last.
2. SceneBuilder places the pile at x = 6 on the grass past the road, at the chicken's
   ground height, sorting order 4 (behind the chicken).
3. Space press checks two things at press time: the gap between the chicken's renderer
   bounds and the pile's base footprint is ≤ 0.5 × the chicken's width, and the chicken
   faces the pile (`flipX` = facing right). The pile's footprint is a fixed `halfWidth`
   because the strays in later states spread across the whole cell.
4. The pile now advances when that peck reaches its head-down frame, not on the press.
   Pecks are queued as `Queue<bool>`, each remembering whether it was aimed at the corn.

### Win trigger (`b6813ad`)
5. The win fired at x = 3 and disabled the controller before the chicken could reach the
   corn. Added `GameManager.winTriggerEnabled` (default false) to turn it off for now.

### Corn shadow (`535856a`)
6. Stripped the soft baked drop shadow from all three corn sheets with a PIL script:
   dark translucent pixels (max channel < 60) cleared, kernel edges blended over the
   shadow un-blended.
7. Drew a flat oval under states 0–3 in the chicken shadow's style: RGB (93, 80, 68),
   alpha 129, 17px tall, centred on the ground line (y = 269 in the cell), as wide as
   the pile (375px for states 0–2, 313px for state 3). State 4 has no shadow.
8. Pile half-width corrected to 187.5px (0.79 world units); the old 206px included the shadow.

### Build tooling (`003aa19`, `e09330d`)
9. Added `build.sh`: runs `SceneBuilder.BuildScene` then `PlayerBuilder.BuildWindows`,
   prints log errors on failure, and refuses to start while the Editor has the project
   open (`Temp/UnityLockfile`).
10. SceneBuilder now rewrites the saved scene with stable file IDs (FNV-1a hash of the
    hierarchy path + component type + index), sorted by ID, then reopens it. Two rebuilds
    now produce a byte-identical `MainScene.unity`.

### Controls (`882895b`)
11. From a standstill, a left/right press turns the chicken immediately and only starts
    running after `turnHoldTime` (0.12s), so a tap turns in place.

### Cleanup (`c5a6f00`)
12. Removed unused sprites: `chicken_pecking.png`, `chicken_run_1_classic_4frame.gif`,
    `chicken_run_2_smooth_12frame_sheet.png`, `corn.jpg`. Corn sheet variants 1 and 2 kept.

### Explanations given
- CLI commands for the scene rebuild and the player build (WSL and PowerShell).
- `0f` is a float literal, not an enum; table of C# numeric suffixes.

## Open items
- `c5a6f00` (sprite cleanup) is not pushed yet.
- The win trigger is off; it needs a new condition (e.g. right level edge) before it
  can come back without blocking the corn.
- The 0.12s turn delay applies even when the chicken already faces the pressed direction;
  the user was offered a variant that only delays a turn-around.
