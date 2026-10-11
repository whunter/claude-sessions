# Handoff — Ballot Guides (Nov 3, 2026)

## Current state

Two guides are finished, each with a Markdown source and a PDF copy:

```
C:\Users\wleeh\Desktop\ballot_guides     (WSL: /mnt/c/Users/wleeh/Desktop/ballot_guides)
├── cburg-ballot-guide-nov-2026.md / .pdf      # 35 S Central Dr, Christiansburg 24073 — Montgomery Co. ballot B1, VA-9
└── staunton-ballot-guide-nov-2026.md / .pdf   # 35 Woodland Dr, Staunton 24401 — City of Staunton, VA-6
```

The Windows Desktop now points to `C:\Users\wleeh\Desktop` (no longer OneDrive).
Per the user's CLAUDE.md, never write to a OneDrive path, and flag any file whose
path contains OneDrive.

## Making another guide

1. Naming: `<place>-ballot-guide-nov-2026.md` in the folder above. Ask for the prefix,
   or follow the user's instruction (e.g. "cburg-", "staunton-").
2. Structure (copy an existing guide): title; voter address / district / prepared
   lines; a callout on local quirks with links to the local registrar and
   elections.virginia.gov; then one `##` section per race with a `###` per candidate
   (bio paragraph, then platform paragraph); local referenda; the three statewide
   amendments; Sources.
3. Statewide pieces are identical everywhere and can be reused: the U.S. Senate section
   (Warner vs. Mizusawa) and the three constitutional amendments.
4. Congressional district: the April 2026 redistricting amendment was struck down by
   the Supreme Court of Virginia, so the old map applies. Confirm with
   `elections.virginia.gov/media/redistricting/maps/<Locality>.pdf`.
5. Watch for same-named places in other states. "Staunton" search results included
   Staunton, Illinois.

## Building the PDF (from WSL)

`python3-venv`, `reportlab` and `poppler` are not installed. Install `markdown` into a
throwaway directory with `pip install --target <dir> markdown`. Convert the Markdown
to HTML with extensions `extra`, `sane_lists`, `nl2br`, using inline CSS (Georgia
serif, 11pt, Letter page with 0.75in margins, rule under h2, grey blockquote). Write
the HTML next to the `.md` and print it:

```
"/mnt/c/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf='C:\Users\wleeh\Desktop\ballot_guides\<name>.pdf' 'C:\Users\wleeh\Desktop\ballot_guides\_tmp.html'
```

Run it from `/mnt/c` (not a UNC working directory), then delete `_tmp.html`. Check
the result with the Read tool.

## Open items

- Staunton: confirm the polling place and sample ballot for 35 Woodland Dr. The
  ci.staunton.va.us site blocks automated fetches (HTTP 403).
- Staunton: Council candidates' 2026-specific platforms (beyond support for the sales
  tax) and Jordan Zipser's background were not found.
- OneDrive may still show Desktop backup as on in its settings. A leftover
  `C:\Users\wleeh\OneDrive\Desktop\desktop.ini` remains.
