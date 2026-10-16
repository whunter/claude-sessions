# Handoff — Chicken Game (Unity): console-readiness audit, items #8 and #13 remaining

## Current state

`main` is at `90b862c` locally; `origin/main` (https://github.com/whunter/chicken-game.git)
is at `27014ae`, three commits behind (`261a9a9` LFS, `912bc26` company name, `90b862c` IL2CPP).
Untracked: `Assets/Art/Characters/ChickenAngle.psd(.meta)` (the user's art; don't commit unasked)
and `Assets/Resources.meta` plus an empty `Assets/Resources/` (cause unknown).

The full audit and what was done are in
`/home/wlh/claude-sessions/2026-10-16-unity-audit/summary.md`; the commits hold the diffs.

## Working agreement

The user asked for the items one at a time, **stopping after each** so they can review
status and context. Commit after each item; don't push without asking.

## Next items

- **#8:** `Assets/Scripts/WindowSetup.cs` forces `FullScreenMode.MaximizedWindow` before
  every scene load. Wrap it in a PC-only `#if` (`UNITY_STANDALONE`, and decide about
  `UNITY_EDITOR`). Also note that `Assets/Editor/PlayerBuilder.cs` sets
  `PlayerSettings.fullScreenMode`/`resizableWindow` at build time. Eventually this belongs in a
  persisted settings menu (Steam Deck).
- **#13:** `git rm -r Backups/` (tracked: `Backups/Sprites/ChickenRunningSheet.png` + `.meta`).
  It sits outside `Assets/`, so Unity doesn't care. Look at it before deleting.

## Open asks to the user
- Playtest the IL2CPP build through a full loop. The log is
  `%USERPROFILE%\AppData\LocalLow\ShiftlessFreeloader\ChickenGame\Player.log`.
- Pick further audit items (#6 async/user-scoped `ISaveStore` is the suggested next design task).

## Gotchas
- Close the Editor before `./build.sh` or batch runs. Wrap Unity runs in `timeout`, and
  `[Licensing::Module] Error: Access token is unavailable` is harmless noise.
- If the scripting backend changes, delete `Build/` first or the build fails.
- WSL `sudo` needs a password; `!` commands can't prompt for it.

## Suggested skills
- `mattpocock-skills:codebase-design` for #6/#7 (async save store, platform services seam).
- `mattpocock-skills:domain-modeling` to record decisions as ADRs in `docs/adr/` (e.g. LFS, IL2CPP, platform layer).
- `unity:unity-cli` for headless Editor/build operations.
- `unity:localization`, `unity:manage-sprite-atlas` if items #10/#11 are picked up.
