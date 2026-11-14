# Hand-off: McClung Genealogy

## State
Done. Both deliverables are in `~/Documents/s/genealogy/`:
- `McClung_Family_Tree.pdf`
- `McClung_Family_Research.md`

The HTML source for the PDF was in the session scratchpad (temporary). To change the chart, rebuild it from the markdown data, or ask for the HTML to be saved into the genealogy folder.

## Re-rendering the PDF
```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --no-pdf-header-footer --print-to-pdf=McClung_Family_Tree.pdf chart.html
```

## Access notes
- findagrave.com and werelate.org block WebFetch (403). Use Claude in Chrome (`get_page_text`). For memorial links, run a JS snippet that collects `a[href*="/memorial/"]` and keeps only entries containing a year range. Returning only bare IDs got blocked as "cookie/query string data."
- The oocities.org/wvgenealogy pages (aqwg38, 49, 107, 138) are fetchable directly.

## Open threads / next steps
1. Unopened leads: WeRelate's family page for John McClung & Rebecca Stuart, the WeRelate source page for the 1904 *McClung Genealogy* (free online copies), the rootsweb ~rootsr/138.htm letter, WikiTree McClung-737, and a Highland County Historical Society PDF.
2. Not yet opened on Find a Grave: siblings' memorials for David Gwin McClung, Silas Brown McClung, Frances Sieg Wallace, and Lucy Blair.
3. Primary-record checks:
   - Rockbridge chancery suit *Moore v. McClung's Heirs* (Library of Virginia Chancery Index)
   - Bath Co. Will Book 4:129
   - Montgomery's DAR application
   - Louis M. McClung's CSR (Fold3)
4. Possible extensions: trace the families that married in further back (Gwin → Robert Gwin/Kincaid; Reamer → Hinton; Pullin → Rodgers), or the Hunter/Link lines.
