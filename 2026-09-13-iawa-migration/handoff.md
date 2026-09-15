# Handoff — iawa-migration

## Context
IAWA collection `Ms1990_007_Leviseur` on S3 (`s3://vtdlp-pprd.img.cloud.lib.vt.edu/iawa/Ms1990_007_Leviseur/`) was analyzed for simplification opportunities. See `session-summary.md` for the full writeup.

## Bottom line
~44% of the collection's storage (~21.1 GB of ~48.4 GB) is a redundant duplicate. The ten `Ms1990_007_Folder1/` … `Ms1990_007_Folder10/` subdirectories each contain a full re-copy of the tile pyramid + IIIF manifest/canvas/annotation/sequence JSON + collection manifest for their items — identical in content to what already exists (correctly, and merged) at the collection root. Confirmed via `diff` on `manifest.json` and a `canvas/p1.json` between root and `Folder1`; only the `@id` URL prefixes differ.

## Next steps (not yet done)
1. **Verify nothing references the `FolderN` paths before deleting anything.** Check:
   - The finding-aid / discovery system (e.g., Blacklight, DSpace record) for any manifest URLs pointing at `.../Ms1990_007_FolderN/...` rather than the root path.
   - Any cached/indexed IIIF manifest links (search engines, viewers) that might have picked up the `FolderN` URLs instead of root ones.
2. **If confirmed safe, delete the 10 `Ms1990_007_FolderN/` directories** (`aws s3 rm --recursive` per directory, or a batch delete). This reclaims ~21 GB and removes roughly half the object count (from 572,006 down to ~250,000).
3. **Architectural follow-up (optional, larger scope):** consider whether this collection (and others ingested the same way) should move from static pre-rendered IIIF tile pyramids (~533 tiny JPGs per page) to a dynamic IIIF image server (Cantaloupe/IIPImage) backed by pyramidal TIFF/JP2 masters. That would cut the ~321,000 canonical tile files down to ~602 master files, but requires image-server infrastructure — out of scope for a simple S3 cleanup.
4. **Check whether other IAWA collections in this S3 bucket have the same `FolderN` duplication pattern** — if this collection got it from a specific ingest step, others processed the same way likely have it too, and it may be worth a bucket-wide audit/cleanup script rather than fixing this one collection by hand.

## Useful commands used this session
```bash
# Full recursive listing
aws s3 ls s3://vtdlp-pprd.img.cloud.lib.vt.edu/iawa/Ms1990_007_Leviseur/ --recursive > full_listing.txt

# Size of root tiles/ vs each FolderN/tiles/
awk '$0 ~ /Leviseur\/tiles\// {s+=$3} END {print s/1024/1024" MB"}' full_listing.txt
for n in 1 2 3 4 5 6 7 8 9 10; do
  awk -v n=$n '$0 ~ ("Folder"n"/tiles/") {s+=$3} END {print "Folder"n": "s/1024/1024" MB"}' full_listing.txt
done

# Diff a sample duplicated manifest to confirm content equality
aws s3 cp s3://vtdlp-pprd.img.cloud.lib.vt.edu/iawa/Ms1990_007_Leviseur/Ms1990_007_F001_001_Fleischmann_Dr/manifest.json m_root.json
aws s3 cp s3://vtdlp-pprd.img.cloud.lib.vt.edu/iawa/Ms1990_007_Leviseur/Ms1990_007_Folder1/Ms1990_007_F001_001_Fleischmann_Dr/manifest.json m_folder1.json
diff m_root.json m_folder1.json
```

## Files
- `session-summary.md` — full analysis and findings
- No code or infrastructure changes were made this session; it was investigation only.
