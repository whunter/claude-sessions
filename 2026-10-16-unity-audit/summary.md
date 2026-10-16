# Session Summary — Chicken Game: Console-Readiness Audit

**Date:** 2026-10-16
**Project:** `C:\Users\wleeh\UnityProjects\ChickenGame` (WSL: `/mnt/c/Users/wleeh/UnityProjects/ChickenGame`, symlinked as `~/chicken-game`)
**Remote:** https://github.com/whunter/chicken-game.git (`origin/main` at `27014ae`; `261a9a9`, `912bc26`, `90b862c` committed locally, not pushed)

## Context

The user asked how to improve the project setup for a 2D platformer that will ship on
Xbox, PlayStation, Nintendo, Steam and Game Pass. The `new-unity-project` skill was
invoked, but the project already existed, so the session audited it instead of
bootstrapping. Already in good shape: Unity 6000.6.3f1, URP 2D, Input System (new only),
UI Toolkit, asmdefs with EditMode/PlayMode tests, ADRs, Unity-aware `.gitattributes`,
and saves behind `ISaveStore`.

## The audit (15 recommendations)

Do now:
1. Apply to ID@Xbox (covers Game Pass), PlayStation Partners, Nintendo Developer Portal and
   Steamworks; console SDKs and Unity add-ons come only through them under NDA. Console
   deployment probably needs Unity Pro (unverified).
2. Move to an LTS Unity version that every console add-on supports (unsure whether 6000.6 is LTS).
3. Git LFS for binaries.
4. Set the company name (it is part of `persistentDataPath`).
5. IL2CPP on PC too, to find stripping/AOT problems early.

Architecture for cheap console ports:
6. Make `ISaveStore` async and user-scoped (GDK connected storage, PS/Switch save APIs).
7. A platform services layer: user/profile, controller pairing, achievements, controller
   disconnect, suspend/resume and overlay focus loss.
8. Limit `WindowSetup.cs` (forces a maximized window every launch) to PC.
9. Cert rules: per-platform button glyphs, Nintendo confirm/cancel swap, TV safe areas,
   save indicator, text size, loading times, remapping.
10. Treat Switch as the performance floor; sprite atlases, per-platform texture compression,
    frame pacing (vSync is off on the Very Low and Low quality levels).
11. Localization early.

Housekeeping:
12. CI via GameCI on GitHub Actions; console builds need a self-hosted machine.
13. Remove `Backups/` from the repo.
14. Strip unused engine modules from the manifest.
15. Age ratings through IARC.

The user chose **3, 4, 5, 8 and 13**, one at a time with a stop after each.

## What was done

### #3 Git LFS (`261a9a9`)
- WSL git had no LFS. Sudo needs a password, which the `!` prefix can't prompt for, so
  Claude first unpacked Ubuntu's `git-lfs` package into `~/.local/bin`. The user then
  installed it with sudo, and the `~/.local/bin` copy was removed.
- `git lfs install`; `.gitattributes` binary block (`png jpg jpeg gif psd wav mp3 ogg fbx ttf otf`)
  changed from `binary` to `filter=lfs diff=lfs merge=lfs -text`.
- `git add --renormalize .` turned the latest versions of the 26 tracked binaries into LFS
  pointers. History was **not** migrated, so `.git` (59 MB) won't shrink.

### #4 Company name (`912bc26`)
- `companyName: ShiftlessFreeloader`; `applicationIdentifier: Standalone: com.shiftlessfreeloader.chickengame`.
- A headless open confirmed Unity loads the change and doesn't rewrite it.
- Windows saves moved from `LocalLow\DefaultCompany\ChickenGame` to `LocalLow\ShiftlessFreeloader\ChickenGame`.

### #5 IL2CPP (`90b862c`)
- The user installed the Windows Build Support (IL2CPP) module and VS Build Tools 2022 with the
  C++ workload (VS Community 2026 is also present).
- `scriptingBackend: Standalone: 1`.
- The first build failed because `Build/` held an earlier Mono build. Claude deleted `Build/`
  (player output only), and the rebuild succeeded in about 2.5 minutes.
- The player launched, initialized D3D12 and input, and loaded the first scene with no
  exceptions. **Gameplay beyond the title screen was not tested**; the user was asked to
  play a full loop (start → level → pause → quit → relaunch so it loads the save).
- Builds now also produce `Build/ChickenGame_BackUpThisFolder_ButDontShipItWithYourGame` (debug symbols).

### Not yet done
- #8 `WindowSetup.cs` limited to PC.
- #13 remove `Backups/` (holds `Backups/Sprites/ChickenRunningSheet.png` + `.meta`).

## Loose ends
- An empty `Assets/Resources/` folder and its `.meta` appeared at the time of the first
  (failed) IL2CPP build. The cause is unknown; it's left untracked.
- `Assets/Art/Characters/ChickenAngle.psd` (the user's, 4.5 MB) is untracked. When added, it will go to LFS.
- The three local commits are unpushed. The first push uploads about 26 LFS objects.
