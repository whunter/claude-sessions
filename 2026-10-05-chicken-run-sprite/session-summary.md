# Session summary: running-chicken sprite from chicken.png

Dates: 2026-10-04 to 2026-10-05
Working directory: `/Users/whunter/Pictures` (not a git repository, so nothing was committed there)

## Goal

Turn `chicken.png` (a photo of a carved wooden chicken with its legs spread wide) into an
animated running sprite. The source image is the "extreme" pose of the stride; intermediate
poses are made by reducing the angle between the legs. Five versions were requested for review,
as GIFs in `./chicken_running`.

## What was built

All output is in `/Users/whunter/Pictures/chicken_running/`:

| File | Description |
| --- | --- |
| `chicken_run_1_classic_4frame.gif` | 4 frames (spread, half, gathered, half), 90 ms per frame |
| `chicken_run_2_smooth_12frame.gif` | 12 frames, cosine-eased scissor, 40 ms per frame |
| `chicken_run_3_bounce.gif` | as 2, with twice the lift |
| `chicken_run_4_bounce_rock_squash.gif` | as 3, plus body rock and squash/stretch |
| `chicken_run_5_gallop.gif` | 16 frames, legs slightly out of phase, forward lean, ground streaks |
| `chicken_run_2_smooth_12frame_sheet.png` | sprite sheet of version 2 for use as a game asset |
| `make_chicken_run.py` | the generator that produces all of the above |

GIF frames are 479x614 with a transparent background (the source is 1652x1937, rendered at 25%).

The sprite sheet is 1916x1842: 12 cells of 479x614 in a 4x3 grid, reading order, lossless RGBA
PNG with smooth 8-bit alpha. It includes the ground shadow at 90% opacity (it is opaque in the
GIFs).

## How the generator works

1. Segments the two orange legs from the body by colour, and keeps the largest component of each.
2. Rebuilds the body outline where the legs were attached (cubic fit of radius against angle
   about the body centre), so no bumps are left at the original hip positions.
3. For each frame, rotates each leg about its hip pivot and slides the pivot along the smoothed
   bottom edge of the body, composites legs behind the body, and adds the shadow.
4. Writes GIFs with one shared 255-colour palette, and the sprite sheet as RGBA PNG.

## Changes requested along the way

- At the extremes of the stride the whole chicken lifts slightly and the feet float above the ground.
- As the legs close, the hips move closer together along the bottom edge of the body.
- Bumps at the original hip positions removed.
- In the gathered pose the legs are vertical and close together, with a small gap between the feet.
- macOS refused to open one of the GIFs. The GIF data was valid; the file carried a quarantine
  flag from Preview and an "Open With: Google Chrome" override, which survived because the files
  were overwritten in place. The generator now deletes each output before writing it.
- Sprite sheet of version 2 with a 10% more translucent shadow.

## Verification

- Poses were checked on still frames and contact sheets, not by watching playback.
- All five GIFs decode fully with macOS ImageIO and have no extended attributes. Whether the
  rejected file now opens was not confirmed in an app.
- The sprite sheet was checked by compositing it over a solid colour. It has not been loaded in a
  game engine.
