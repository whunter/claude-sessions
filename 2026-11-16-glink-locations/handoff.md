# Hand-off: glink spatial and location metadata

## State
- `~/dev/dlp/assets/glink/20261116_glink_archive_metadata.csv` now has `spatial` and `location` (`lat||long`) columns, with 51 of the 136 rows filled in.
- `20261116_glink_archive_metadata_backup.csv` in the same folder is the copy from before these columns were added.
- The assets folder is not a git repo, so nothing there is under version control.
- To regenerate the columns, run `python3 add_locations.py <csv>` against a copy of the backup. The script is in this folder. It adds both columns and refuses to run if they already exist. It writes CRLF line endings with no trailing newline, matching the original file.

## Open items and decisions to review
- **Sketchbooks 001001–001007 and 001009 are empty.** Each covers several trips or places, or no place at all, so a single value doesn't fit. Per-page CSVs in `docs/` (`glink0010NN.csv`) would be the place to record per-page locations if wanted.
- **Locations inferred from other rows:**
  - 002002 S.W. Link House → Quicks Mill, taken from 002084 and 002123.
  - 002095 Howdy Partner → Staunton, because 002012 places the curator's childhood home there.
- **Borderline rows:**
  - 002117 → Staunton, based only on the photo studio's location.
  - 002129 → "Portugal", from the inscription on the drawing.
  - 001008 → Outer Banks, the only place the sketchbook names.
  - 002061 uses GNIS "Great Harbor" (the harbor at Woods Hole).
- **Left empty on purpose:**
  - 002016 and 002017 ("likely Spain and Portugal").
  - 002111, a copy of Hathaway's Joshua Winsor house painting, which shows Duxbury, MA, but no place is named in the metadata.
- **Torre da Aldeia** (002040) wasn't found in OpenStreetMap, so the row uses the centre of Albufeira.
- **Non-GNIS sources:** coordinates for places outside the US come from OpenStreetMap, not GNIS. Swap in NGA GNS (GEOnet Names Server) values if a GNIS-equivalent source is required.
- **McClung farm:** coordinates were supplied by the curator (`38.27010472896028||-79.54108003201007`) and apply to 002029 and 002036. 002030 keeps the GNIS point for Clover Creek Presbyterian Church.
