# Writing `description` for GLink archive records

You are writing the `description` field for records in a digital library collection of artwork by Gretchen Link (née Gretchen Hitt): paintings, sketchbooks, photos and a silhouette set. Each record already has `alt_text` (a one-line accessibility text) and `visual_description` (a detailed literal account of what is visible). Your job is to write the `description`, the public-facing, catalog-style summary of the item.

## Input

You get one batch JSON file. Each record holds the existing metadata fields plus `images`, a list of absolute JPG paths. **Look at every image in the list with the Read tool.** There are never more than 10.

- `kind: "single"`: up to 10 single-image records. Write one description per record.
- `kind: "multi"`: one multi-image record (a sketchbook, a 2-image painting or a silhouette set). `images` is a sample of no more than 10 pages, always including page 1. `page_files` lists CSVs with alt text and visual descriptions, tags and dates for **every** page. Read all of them so the description covers the whole item, not only the sampled pages.

## What a good description does

- **Says what the item is and what it shows**: subject, setting, composition, and the mood or handling where that is evident (loose washes, careful line, bold color).
- **Adds context the other fields lack**: inscriptions, signatures, dates written on the work, places named, recurring subjects. Use `date`, `date_notes` and the page-level data where useful.
- **Does not repeat `visual_description`** line by line. Summarize and interpret lightly; don't inventory every object.
- **Stays factual.** Don't guess at identities, places or meanings that the image or metadata don't support. When something is uncertain, say "appears to" or leave it out. Don't praise the work.
- **Length:**
  - Single-image records: 2–4 sentences (roughly 40–90 words).
  - Sketchbooks and other multi-image records: 4–7 sentences (roughly 80–160 words). Describe the range of contents, the main subjects and places, the date span, and notable pages (title pages, inscriptions, later additions).
- **Style:** plain prose in a neutral catalog voice, present tense, American spelling. No markdown, no bullet points, no line breaks. Refer to the artist as "the artist" or "Gretchen Link"; don't open every description with "This painting…". Don't state the size or the medium as a bare fact unless it adds something (e.g. "painted on velvet").

## Output

Write a JSON file to the output path given in your task, holding a list of objects:

```json
[{"identifier": "glink002041", "description": "..."}]
```

One object per record in the batch, in the same order. Use the Write tool. Don't change any other file. In your final reply, just confirm the file was written and list any records where the image disagreed with the existing metadata (one line each), or say "no discrepancies".

## Signatures

Every signature in the collection is some form of the artist's name, Gretchen Hitt Link. It is usually "G Link", sometimes "Gretchen Link", "G. Link", "Gretchen Hitt" or "G.L.H.". If you can read the signature, quote it as written. If it's too faint to read, say "faintly signed" and don't guess other letters or names.
