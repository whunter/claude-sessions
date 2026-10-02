# Handoff: schema-generated OpenSearch mappings and pprd date audit (dlp-access-next-cdk)

Follow-up to `../2026-09-30-search-field-types/`. Repo: `~/dev/dlp/access/dlp-access-next-cdk`, branch `whunter/search-field-types`, 4 commits ahead of `origin/whunter/search-field-types`, **not pushed**. Nothing was deployed, and no table or index was modified (the pprd Archive table was only scanned).

Record-level data from the scan is deliberately not in this folder. The list of bad fchs records is at `~/Desktop/fchs-bad-dates.csv` (local only).

## What changed

`infra/lib/search-mappings.ts` now generates the `archive` and `collection` index mappings from `infra/schema/schema.graphql` at synth time, ported from the Amplify app's `amplify/data/opensearch-mappings.ts` (dlp-access). The hand-written `infra/schema/opensearch/*.json` files are deleted. `graphql` is a new dependency in `infra/`.

| Commit | Change |
|---|---|
| `87a564f` | Generate the mappings from the schema |
| `ab88596` | Drop `yyyy/M`, `yyyy-M`, `yyyyMM` from the date formats |
| `28f9e69` | Add `M/d/yyyy` |
| `9ea64c7` | Drop `epoch_millis` |

Every date field (`date`, `start_date`, `end_date`, `embargo_start_date`, `embargo_end_date`, plus any `AWSDateTime`/`AWSDate` field) is mapped with `ignore_malformed: true` and this format:

```
yyyy/MM/dd HH:mm:ss||yyyy/MM/dd||yyyy/MM||yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||yyyy-MM||yyyy||M/d/yyyy||strict_date_optional_time
```

Typecheck and Jest pass (80 tests). The Jest tests only check the generated mapping objects; no format has been tried against a live domain.

## Behaviour changes to know about

- **`Archive.date` is a date, not text.** It sorts on the field itself with numeric page tokens (`numericSortFields` picks it up automatically).
- **`AWSJSON` fields are unindexed objects** (`enabled: false`): `alt_text`, `extracted_text`, `visual_description`, `archiveOptions`, `manifest_file_characterization`, `collectionOptions`, `ownerinfo`. They stay in `_source`. None is in the resolvers' `searchFields`.
- **Mappings are `dynamic: false`.** Attributes not in the schema are stored but not indexed. That includes `createdAt`/`updatedAt`, which Amplify's generator maps and this one doesn't, because the schema here doesn't declare them.
- **The format list now differs from Amplify's**, which still has `yyyy/M`, `yyyy-M`, `yyyyMM` and `epoch_millis`, and lacks `M/d/yyyy` and `strict_date_optional_time`.
- **Existing indexes keep their old mappings** until deleted and reindexed.

## Next steps

1. **Push the branch** when ready (4 commits).
2. **Verify on the next deploy:**
   - `M/d/yyyy` accepts one- and two-digit months and days.
   - Paging a search sorted on a date field still works without `epoch_millis` in the format. The resolver sends the page token and the `missing` sort value as JSON numbers; OpenSearch should take those as epoch millis without consulting the format.
3. **Decide on date normalization in the streaming Lambda** (proposed, not built). See "Proposal" below.
4. **Fix the bad source records in pprd** (see the audit).
5. **Decide whether `createdAt`/`updatedAt` should be indexed.**

## pprd date audit

The pprd Archive table, 10,487 records, scanned 2026-10-01/02.

- No value in any date field is formatted `yyyy/M`, `yyyy-M` or `yyyyMM`, and none is an epoch number.
- `embargo_start_date` and `embargo_end_date` are not set on any record.
- `date` is set on 5,422 records, `start_date` on 7,582, `end_date` on 836. 5,418 records have both `date` and `start_date`; 2,164 have only `start_date`; 4 have only `date`.
- `date` is multi-valued in 37 records.
- Real years all fall in 1700-2099.

`date` shapes (`d` = digit, counts are values):

| Shape | Count | Parsed by the current formats |
|---|---|---|
| `dddd-dd-dd` | 3,505 | yes |
| `d/dd/dddd`, `dd/dd/dddd`, `d/d/dddd`, `dd/d/dddd` | 1,025 | yes, by `M/d/yyyy` (unverified live) |
| `dddd` | 386 | yes |
| `dddd-dd` | 176 | yes |
| `d.ddddddddd` | 162 | no |
| `dddd-dd-dd/dddd-dd-dd` | 108 | no (range) |
| `dddd/dddd` | 42 | no (year range) |
| `~dddd` | 28 | no |
| `dddd-dd/dddd-dd` | 9 | no (range) |
| `dddX` | 5 | no |
| `dddd.dd.dd`, `c. dddd` | 2 each | no |
| 13 one-off shapes: mixed-precision ranges, `dddd?`, month-name dates, free text | 13 | no |

Month-first is safe for the slash dates: 726 have a second part above 12, none have a first part above 12.

`start_date` shapes: `dddd/dd/dd` 7,055; `dddd` 426; `dddd-dd-dd` 81; `dddd-dd` 19; free text 1.
`end_date` shapes: `dddd/dd/dd` 553; `ddd/dd/dd` 162; `dddd` 117; `dddd-dd-dd` 3; free text 1.

Bad source data:

- **162 records in one fchs batch** share the same three bad values: a decimal number in `date`, a year-7999 `start_date` and a three-digit-year `end_date`. The `start_date` is a valid `yyyy/MM/dd`, so it will be indexed and sort after every real date. Listed in the Desktop CSV.
- **About 29 records with a `start_date` in May 1905** although `date` is a 20th-century year: the year was read as a spreadsheet day number. Counted from shape pairs (year-shaped `date` with a `dddd-dd-dd` `start_date`), not individually checked.
- **Invented precision in `start_date`/`end_date`:** approximate dates (`~dddd`, `dddX`) were expanded to full dates with an arbitrary month and day.
- **Test/typo records:** one with placeholder text in all three fields, one with a misspelled "unknown" in `date`.

## Proposal (not built)

The mapping can only accept or drop a string; it can't reject a well-formed but implausible date. To be lenient on format but strict on plausibility, normalize in `infra/lambda/opensearch-streaming/`:

1. Parse each value leniently (the shapes above; the approximate ones are EDTF notation: `X`, `~`, `?`, `/`), reject years outside a plausible window, emit ISO values. Originals stay in `_source`.
2. Add a derived `date_range` field (`gte`/`lte`) so a year, a year-month, `dddX`, a year range and `~dddd` are indexed as intervals, with an "approximate" flag for `~`, `c.` and `?`.
3. Keep one sortable date (the interval start), derived from `date` rather than trusting the stored `start_date`.
4. The mapping's format list could then shrink to `strict_date_optional_time`, with `ignore_malformed` as a backstop.
