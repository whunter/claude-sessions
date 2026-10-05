# Hand-off: running-chicken sprite

## State

Everything requested so far is done. There is no open task. Awaiting review of the five
versions and of the sprite sheet.

## Where things are

- Source image: `/Users/whunter/Pictures/chicken.png` (unmodified)
- Outputs and generator: `/Users/whunter/Pictures/chicken_running/` (see `session-summary.md`)
- `/Users/whunter/Pictures` is not a git repository; the only copy of the generator is
  `chicken_running/make_chicken_run.py`.

## Running the generator

The system `python3` has no Pillow. The session used a throwaway virtualenv in a temporary
scratch directory, which will not persist. To recreate it:

```sh
python3 -m venv /tmp/chicken-venv
/tmp/chicken-venv/bin/pip install pillow numpy scipy
cd /tmp && /tmp/chicken-venv/bin/python /Users/whunter/Pictures/chicken_running/make_chicken_run.py
```

Versions used: Pillow 12.3.0, NumPy 2.5.3, SciPy 1.18.1.

Things to know before running it:

- `SRC` and `OUT` are absolute paths at the top of the script.
- It regenerates all five GIFs and the sprite sheet every time.
- It also writes preview files `sheet_1.png`, `sheet_4.png` and `sheet_5.png` into the current
  directory, so run it from somewhere disposable rather than from `chicken_running`.

## Knobs in `make_chicken_run.py`

| Name | Meaning | Current value |
| --- | --- | --- |
| `SCALE` | output size relative to the source | 0.25 |
| `PIV` | hip pivot of each leg, source pixels | L (432, 1580), R (1232, 1516) |
| `GAP` | space between the feet in the gathered pose, source pixels | 50 |
| `INSET` | how far the hips tuck into the body when gathered | 34 |
| `LIFT` | how far the body rises at full spread, source pixels | 60 |
| `CLOSED` | leg spread at the gathered pose (0 = vertical) | 0.0 |
| `SHADOW_A` | shadow alpha in the sprite sheet | 230 (90%) |
| `sprite_sheet(..., cols)` | sprite sheet columns | 4 |

`pose(sL, sR, dy, tilt, sq, shadow, dashes, shadow_alpha)` renders one frame; `sL`/`sR` are the
fraction of the original leg spread (1 = source image, 0 = straight down).

## Open points

- The macOS "won't open" fix is unconfirmed. The actual error dialog was never seen; the cause
  was inferred from the file's quarantine and Open With attributes. If it recurs, get the exact
  wording of the dialog. Setting "Open With" again on a file Preview has touched may bring it back.
- Preview shows GIF frames as pages rather than animating. Use Quick Look or a browser to watch.
- Sprite sheet frames are at the GIF's 479x614. A sheet at the source's full resolution would
  need `SCALE = 1.0` (cells of about 1916x2456).
- The sheet is frames only; there is no JSON/atlas metadata file. Timing for version 2 is 40 ms
  per frame, 12 frames, looping.
- Only version 2 has a sprite sheet.
