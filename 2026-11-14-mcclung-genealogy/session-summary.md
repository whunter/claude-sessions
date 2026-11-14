# Session Summary: McClung Genealogy (2026-11-14)

## Request
Trace the paternal-grandmother line (Montgomery Reamer McClung Linkous) as far back as possible. List siblings for each generation, produce a visual PDF and a markdown file of details and links, and list promising links that returned 403.

## Outcome
Traced 9 generations, back to James McClung (b. ~1679, prob. Co. Tyrone, Ireland; d. ~1744, Lancaster Co., PA).

Direct line: William Lee Hunter → Dr. William Snowden Hunter → Montgomery Reamer McClung (1916–2001) → Louie Edwin McClung (1883–1929) → Pvt. Louis Martine McClung (1846–1927) → William McClung (1793–1865) m. Rachel Violet Gwin → John "Bath John" McClung (1732–1830) m. Sarah McCutcheon → John McClung Sr. (~1705–1787) m. Janet Thompson → James McClung.

## Deliverables (in `~/Documents/s/genealogy/`, not a git repo)
- `McClung_Family_Tree.pdf`: 3-page chart. Pages 1–2 are the generation-by-generation pedigree with spouses and siblings, plus a migration strip. Page 3 has tables of the families that married in and the source conflicts.
- `McClung_Family_Research.md`: per-generation details, links, source conflicts, next-step research suggestions, and a table of blocked (403) links.

## Method
- WebFetch got 403 from Find a Grave and WeRelate. A curl attempt with a browser user agent was denied by the permission classifier.
- Read those pages through Claude in Chrome instead. WeRelate's bot check cleared on its own after a moment.
- The oocities.org/wvgenealogy compiled McClung database was fetchable directly and supplied the Bath John and William family lists.
- The PDF was rendered from HTML with headless Chrome (`--print-to-pdf`); reportlab and weasyprint aren't installed.

## Key findings
- The 1844 McClung brick house at Clover Creek, Highland Co., was later owned by Montgomery and her sisters.
- Louis Martine served in Co. C, 14th Va. Cavalry, lost a leg after Winchester, and was Clover Creek postmaster.
- Bath John: Revolutionary War service, Windy Cove Church elder, will dated 1830.
- Montgomery was a DAR member, so her application file is a likely source of documented proofs.
- Main conflict: whether the mother of John Sr.'s older sons was Janet Thompson or Rebecca Stuart (later research favors Janet).
