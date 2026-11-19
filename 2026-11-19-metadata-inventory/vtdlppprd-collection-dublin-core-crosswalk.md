# Collection Metadata → Dublin Core Crosswalk

This maps each header in `vtdlppprd-collection-metadata-template.csv` to its closest **DCMI Metadata Terms** property (`dcterms:`).

- **Source standard:** [DCMI Metadata Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/), DCMI Recommendation, issued 2020-01-20.
- **DC definition / recommended usage:** quoted from the DCMI definition and comment for each term.
- **DC example:** DCMI's term list doesn't include examples. The examples below are illustrative and follow DCMI's recommended practice.
- **Our value:** a real value from the vtdlppprd `Collection` table. The record's `identifier` is given in parentheses. Multiple values are joined with `||`, the same way the ingest CSV joins them. Long values are shortened with "…".
- **Site reference example:** used only for headers vtdlppprd doesn't have values for. It's the example value given for that field in the site's own field reference (`dlp-access/src/data/metadataFieldInfo.json`).
- **Match:** *Exact* means the meaning is the same. *Close* means it's similar but narrower or broader. *Loose* means it's the nearest term, but not really the same thing. *None* means DC has no equivalent; these are app/system fields.
- **In Collection API:** whether the `Collection` type in the GraphQL schema (`dlp-access-next-cdk/infra/schema/schema.graphql`; the old Amplify schema is the same except where noted) returns the field. Fields marked "No" are still saved to DynamoDB, but the site can't read them through the API.

## Summary

| Our header | Dublin Core term | Match | In Collection API |
|---|---|---|---|
| `identifier` | `dcterms:identifier` | Exact | Yes |
| `title` | `dcterms:title` | Exact | Yes |
| `parent_collection_identifier` | `dcterms:isPartOf` | Exact | Yes |
| `collection_category` | — | None | Yes |
| `visibility` | `dcterms:accessRights` | Loose | Yes |
| `archived` | — | None | Yes |
| `explicit_content` | `dcterms:audience` | Loose | Yes |
| `embargo_start_date` | `dcterms:accessRights` | Loose | Yes |
| `embargo_end_date` | `dcterms:available` | Close | Yes |
| `rights_statement` | `dcterms:rights` (URI value) | Exact | No |
| `create_date` | `dcterms:created` | Close | Yes |
| `modified_date` | `dcterms:modified` | Close | Yes |
| `start_date` | `dcterms:date` / `dcterms:temporal` (start of range) | Close | Yes |
| `end_date` | `dcterms:date` / `dcterms:temporal` (end of range) | Close | Yes |
| `date` | `dcterms:date` | Exact | No |
| `display_date` | `dcterms:date` (literal) | Close | Yes |
| `description` | `dcterms:description` | Exact | Yes |
| `creator` | `dcterms:creator` | Exact | Yes |
| `bibliographic_citation` | `dcterms:bibliographicCitation` | Exact | Yes |
| `extent` | `dcterms:extent` | Exact | No |
| `format` | `dcterms:format` | Exact | No |
| `language` | `dcterms:language` | Exact | Yes |
| `location` | `dcterms:spatial` (coordinates) | Close | Yes |
| `provenance` | `dcterms:provenance` | Exact | Yes |
| `related_url` | `dcterms:relation` | Close | No |
| `relation` | `dcterms:relation` | Exact | Yes |
| `repository` | `dcterms:publisher` | Loose | No |
| `rights` | `dcterms:rights` (literal value) | Exact | Yes |
| `rights_holder` | `dcterms:rightsHolder` | Exact | Yes |
| `source` | `dcterms:source` | Exact | Yes |
| `spatial` | `dcterms:spatial` | Exact | Yes |
| `subject` | `dcterms:subject` | Exact | Yes |
| `tags` | `dcterms:subject` | Close | No |
| `type` | `dcterms:type` | Exact | No |

### Headers the ingest accepts that vtdlppprd collections don't use yet

The ingest accepts these headers (`data/headers_keys.json` and `set_attribute` in `dlp-ingest`), but no record in the vtdlppprd `Collection` table has them. Seven item-only headers that the ingest also accepts (`extracted_text`, `visual_description`, `download_link`, `is_format_of`, `format_physical`, `basis_of_record` and `taxonomy`) are left out because they don't apply to collections. Each one is described in [Accepted by ingest, not yet used](#accepted-by-ingest-not-yet-used) below.

| Our header | Dublin Core term | Match | In Collection API |
|---|---|---|---|
| `alternative` | `dcterms:alternative` | Exact | No |
| `contributor` | `dcterms:contributor` | Exact | No |
| `publisher` | `dcterms:publisher` | Exact | No |
| `other_identifier` | `dcterms:identifier` | Close | No |
| `created` | `dcterms:created` | Exact | No |
| `circa` | `dcterms:date` (approximate) | Loose | No |
| `temporal` | `dcterms:temporal` | Exact | No |
| `coverage` | `dcterms:coverage` | Exact | No |
| `medium` | `dcterms:medium` | Exact | No |
| `resource_type` | `dcterms:type` | Close | No |
| `conforms_to` | `dcterms:conformsTo` | Exact | No |
| `license` | `dcterms:license` | Exact | No |
| `embargo_note` | `dcterms:accessRights` | Close | Yes |
| `explicit` | `dcterms:audience` | Loose | No |
| `is_part_of` | `dcterms:isPartOf` | Exact | Yes |
| `belongs_to` | `dcterms:isPartOf` | Loose | No |
| `has_part` | `dcterms:hasPart` | Exact | No |
| `has_format` | `dcterms:hasFormat` | Exact | No |
| `has_version` | `dcterms:hasVersion` | Exact | No |
| `is_version_of` | `dcterms:isVersionOf` | Exact | No |
| `references` | `dcterms:references` | Exact | No |
| `provider` | `dcterms:publisher` | Loose | Old Amplify schema only |
| `alt_text` | `dcterms:description` | Loose | Yes |
| `title_template` | — | None | Yes |
| `filename` | — | None | n/a (not stored) |

### Headers the Collection API doesn't return

The ingest saves these headers to the vtdlppprd `Collection` table, but the site reads collections through the GraphQL API, and the `Collection` type doesn't include these fields. Until the schema adds them, values in these columns are stored but **won't appear on the site**. (Checked against `dlp-access-next-cdk/infra/schema/schema.graphql` and the old Amplify schema on 2026-11-19.)

**Already used in vtdlppprd (8).** These collections have data in these fields that the site can't show:

| Header | Records with a value |
|---|---|
| `date` | 12 |
| `tags` | 6 |
| `rights_statement` | 5 |
| `extent` | 5 |
| `type` | 4 |
| `repository` | 4 |
| `format` | 3 |
| `related_url` | 1 |

**Accepted by the ingest but not used yet (20):** `alternative`, `belongs_to`, `circa`, `conforms_to`, `contributor`, `coverage`, `created`, `explicit`, `has_format`, `has_part`, `has_version`, `is_version_of`, `license`, `medium`, `other_identifier`, `provider`, `publisher`, `references`, `resource_type`, `temporal`. `provider` is the one exception: the old Amplify schema has it, but the CDK schema doesn't.

`filename` isn't on either list. The ingest never stores it; it only uses it to build the thumbnail and manifest paths.

---

## Identification

### `identifier` → `dcterms:identifier` (Exact)
- **DC definition:** "An unambiguous reference to the resource within a given context."
- **DC recommended usage:** "Recommended practice is to identify the resource by means of a string conforming to an identification system."
- **DC example:** `ark:/53696/abc123` or `Ms2008-020`
- **Our value:** `vtac` (vtac)

### `title` → `dcterms:title` (Exact)
- **DC definition:** "A name given to the resource."
- **DC recommended usage:** No comment from DCMI. Use the formal name of the resource.
- **DC example:** `Melita Rodeck Architectural Collection, 1931-2003`
- **Our value:** `Virginia Tech Art Collection` (vtac)

### `parent_collection_identifier` → `dcterms:isPartOf` (Exact)
- **DC definition:** "A related resource in which the described resource is physically or logically included."
- **DC recommended usage:** "This property is intended to be used with non-literal values. This property is an inverse property of Has Part."
- **DC example:** `https://example.edu/collection/CIDA`, the URI of the parent collection.
- **Our value:** `CIDA` (CIDA_JFC)
- **Notes:** DCMI prefers a URI. We store the parent's local identifier and resolve it to an id during ingest.

## Access and status (app fields)

### `collection_category` → no DC equivalent (None)
- **DC definition / usage:** —
- **DC example:** —
- **Our value:** `federated` (vtac)
- **Notes:** This is an internal grouping for the site, set from the ingest form. It doesn't describe the resource.

### `visibility` → `dcterms:accessRights` (Loose)
- **DC definition:** "Information about who access the resource or an indication of its security status."
- **DC recommended usage:** "Access Rights may include information regarding access or restrictions based on privacy, security, or other policies."
- **DC example:** `Open access` or `Restricted to Virginia Tech users`
- **Our value:** `true` (vtac)
- **Notes:** Ours is a true/false switch that shows or hides the record on the site. DC expects a statement about access instead.

### `archived` → no DC equivalent (None)
- **DC definition / usage:** —
- **DC example:** —
- **Our value:** `true` (vtac)
- **Notes:** This is an app status flag. The ingest sets it to `true` unless the CSV gives `false`.

### `explicit_content` → `dcterms:audience` (Loose)
- **DC definition:** "A class of agents for whom the resource is intended or useful."
- **DC recommended usage:** "Recommended practice is to use this property with non-literal values from a vocabulary of audience types."
- **DC example:** `Adults` or `Researchers`
- **Our value:** `false` (LD5655.A3.C3)
- **Notes:** DC has no content-warning property. Audience is the closest one, but ours is a true/false flag.

### `embargo_start_date` → `dcterms:accessRights` (Loose)
- **DC definition:** "Information about who access the resource or an indication of its security status."
- **DC recommended usage:** "Access Rights may include information regarding access or restrictions based on privacy, security, or other policies."
- **DC example:** `Embargoed from 2025-12-04 until 2027-12-04`
- **Our value:** `2025-12-04T06:00:00.010Z` (0867b-22f6-4d)
- **Notes:** DC has no "unavailable from" date. The usual approach is to state the embargo in `accessRights` and put the release date in `available`.

### `embargo_end_date` → `dcterms:available` (Close)
- **DC definition:** "Date that the resource became or will become available."
- **DC recommended usage:** "Recommended practice is to describe the date, date/time, or period of time as recommended for the property Date, of which this is a subproperty."
- **DC example:** `2027-12-04`
- **Our value:** `2025-12-04T07:00:00.010Z` (0867b-22f6-4d)

## Rights

### `rights_statement` → `dcterms:rights` (Exact, URI form)
- **DC definition:** "Information about rights held in and over the resource."
- **DC recommended usage:** "Typically, rights information includes a statement about various property rights associated with the resource, including intellectual property rights. Recommended practice is to refer to a rights statement with a URI. If this is not possible or feasible, a literal value (name, label, or short text) may be provided."
- **DC example:** `http://rightsstatements.org/vocab/NoC-US/1.0/`
- **Our value:** `http://rightsstatements.org/vocab/InC-EDU/1.0/` (CRW)
- **Notes:** This is the URI form that DCMI recommends. (Europeana/EDM also uses `edm:rights` for this.)

### `rights` → `dcterms:rights` (Exact, literal form)
- **DC definition / recommended usage:** same as `rights_statement` above. This is the "literal value" option.
- **DC example:** `Copyright 2007 Virginia Tech. Educational use permitted.`
- **Our value:** `Items in this collection are protected by copyright and/or related rights. You are free to use these items in any way that is permitted by the copyright and related rights legislation that applies to your use…` (Ms2008-020)

### `rights_holder` → `dcterms:rightsHolder` (Exact)
- **DC definition:** "A person or organization owning or managing rights over the resource."
- **DC recommended usage:** "Recommended practice is to refer to the rights holder with a URI. If this is not possible or feasible, a literal value that identifies the rights holder may be provided."
- **DC example:** `Virginia Polytechnic Institute and State University` (or that organization's authority URI)
- **Our value:** `Virginia Polytechnic Institute and State University` (Ms2008-020)

## Dates

### `create_date` → `dcterms:created` (Close)
- **DC definition:** "Date of creation of the resource."
- **DC recommended usage:** "Recommended practice is to describe the date, date/time, or period of time as recommended for the property Date, of which this is a subproperty."
- **DC example:** `2007-04-20`
- **Our value:** `2025/04/11 19:26:30` (LD5655.A3.C3)
- **Notes:** DC means the date the *resource* was made. Our values look like the date the *record or digital collection* was created. The ingest also writes them as `YYYY/MM/DD`, but DC recommends ISO 8601 (`YYYY-MM-DD`).

### `modified_date` → `dcterms:modified` (Close)
- **DC definition:** "Date on which the resource was changed."
- **DC recommended usage:** "Recommended practice is to describe the date, date/time, or period of time as recommended for the property Date, of which this is a subproperty."
- **DC example:** `2024-01-09`
- **Our value:** `2024/01/09 19:33:51` (nmcst)
- **Notes:** This has the same `/` vs ISO 8601 difference as `create_date`.

### `date` → `dcterms:date` (Exact)
- **DC definition:** "A point or period of time associated with an event in the lifecycle of the resource."
- **DC recommended usage:** "Date may be used to express temporal information at any level of granularity. Recommended practice is to express the date, date/time, or period of time according to ISO 8601-1 or a published profile of the ISO standard, such as the W3C Note on Date and Time Formats or the Extended Date/Time Format Specification. If the full date is unknown, month and year (YYYY-MM) or just year (YYYY) may be used. Date ranges may be specified using ISO 8601 period of time specification in which start and end dates are separated by a '/' (slash) character. Either the start or end date may be missing."
- **DC example:** `1931/2003`, `1960-05`, `1957/`
- **Our value:** `1957/2000` (CIDA_JFC)
- **Notes:** This already follows the ISO 8601 range syntax.

### `start_date` / `end_date` → `dcterms:date` or `dcterms:temporal` (Close)
- **DC definition:** `date` is defined above. `temporal` is "Temporal characteristics of the resource."
- **DC recommended usage:** DC has no separate start and end properties. Express the range as one ISO 8601 period, `start/end`, in `dcterms:date`. If the dates are what the collection is *about*, use `dcterms:temporal`.
- **DC example:** `2007/2007` → `start_date` = `2007`, `end_date` = `2007`
- **Our value:** `start_date` = `2007`, `end_date` = `2007` (Ms2008-020)

### `display_date` → `dcterms:date` (Close, literal)
- **DC definition / recommended usage:** same as `date`. DC allows a free-text date, but its recommended practice is ISO 8601.
- **DC example:** `circa 1960s`
- **Our value:** `1957-2000` (CIDA_JFC)
- **Notes:** This is a human-readable version of `date`. A DC export would normally keep only the ISO form (`date`).

## Description and agents

### `description` → `dcterms:description` (Exact)
- **DC definition:** "An account of the resource."
- **DC recommended usage:** "Description may include but is not limited to: an abstract, a table of contents, a graphical representation, or a free-text account of the resource."
- **DC example:** `Correspondence, photographs, and drawings documenting the architectural practice of …`
- **Our value:** `This collection includes featured artwork images from the Miles and Ruth Horton Collection. Donated in the early 2000s, the Miles and Ruth Horton Collection includes artwork from around the world…` (vtac)

### `creator` → `dcterms:creator` (Exact)
- **DC definition:** "An entity responsible for making the resource."
- **DC recommended usage:** "Recommended practice is to identify the creator with a URI. If this is not possible or feasible, a literal value that identifies the creator may be provided."
- **DC example:** `Rodeck, Melita, 1914-2007||Davie, Alan, 1920-2014`
- **Our value:** `Guillaume Corneille, Abraham Rattner and Esther Gentle, Alan Davie, Camille Blair, Ellen Zahorec, Fritz Eichenberg.` (vtac)
- **Notes:** DC expects one value per creator. This record puts six creators in a single string. Separating them with `||` would give six values.

### `repository` → `dcterms:publisher` (Loose)
- **DC definition:** "An entity responsible for making the resource available."
- **DC recommended usage:** No comment from DCMI. As with creator, a URI is preferred over a name.
- **DC example:** `Special Collections and University Archives, Virginia Tech`
- **Our value:** `Special Collections and University Archives, Virginia Tech` (Ms2008-020)
- **Notes:** DC has no "holding institution" property. Many digital libraries map this field to `publisher`. Others use `edm:dataProvider` or MODS `location/physicalLocation`.

### `provenance` → `dcterms:provenance` (Exact)
- **DC definition:** "A statement of any changes in ownership and custody of the resource since its creation that are significant for its authenticity, integrity, and interpretation."
- **DC recommended usage:** "The statement may include a description of any changes successive custodians made to the resource."
- **DC example:** `Donated by Miles and Ruth Horton to Virginia Tech in 2002.`
- **Our value:** `The original object is the property of the Barter Theatre in Abingdon, VA (https://www.bartertheatre.com/). This digital surrogate is made publicly available by the Barter Theatre…` (BTR)

### `bibliographic_citation` → `dcterms:bibliographicCitation` (Exact)
- **DC definition:** "A bibliographic reference for the resource."
- **DC recommended usage:** "Recommended practice is to include sufficient bibliographic detail to identify the resource as unambiguously as possible."
- **DC example:** `James C. and Gertrude (Meredith) Biddle Family Correspondence, Ms2024-105, Special Collections and University Archives, Virginia Tech, Blacksburg, Va.`
- **Our value:** `Researchers wishing to cite this collection should include the following information: [identification of item], [box], [folder], James C. and Gertrude (Meredith) Biddle Family Correspondence, Ms2024-105, Special Collections and University Archives, Virginia Tech, Blacksburg, Va.` (Ms2024-105)
- **Notes:** DC expects only the citation itself. Our value also includes instructions on how to cite.

## Physical / technical

### `extent` → `dcterms:extent` (Exact)
- **DC definition:** "The size or duration of the resource."
- **DC recommended usage:** "Recommended practice is to specify the file size in megabytes and duration in ISO 8601 format."
- **DC example:** `13 pieces`, `2.5 linear feet`, `PT1H30M`
- **Our value:** `13 pieces` (cbcst005)

### `format` → `dcterms:format` (Exact)
- **DC definition:** "The file format, physical medium, or dimensions of the resource."
- **DC recommended usage:** "Recommended practice is to use a controlled vocabulary where available. For example, for file formats one could use the list of Internet Media Types [MIME]. Examples of dimensions include size and duration."
- **DC example:** `image/jpeg`, `application/pdf`
- **Our value:** `image/png` (DH80_S004)

### `language` → `dcterms:language` (Exact)
- **DC definition:** "A language of the resource."
- **DC recommended usage:** "Recommended practice is to use either a non-literal value representing a language from a controlled vocabulary such as ISO 639-2 or ISO 639-3, or a literal value consisting of an IETF Best Current Practice 47 language tag."
- **DC example:** `en`, `en-US`, `eng`
- **Our value:** `en` (Ms2008-020)

### `type` → `dcterms:type` (Exact)
- **DC definition:** "The nature or genre of the resource."
- **DC recommended usage:** "Recommended practice is to use a controlled vocabulary such as the DCMI Type Vocabulary [DCMI-TYPE]. To describe the file format, physical medium, or dimensions of the resource, use the property Format."
- **DC example:** `Collection`, `Still Image`, `Text`
- **Our value:** `Still Image` (DH80_S004)
- **Notes:** For a collection record, DCMI Type has a specific term, `Collection`. Our values describe what the collection *contains*.

## Coverage (place)

### `spatial` → `dcterms:spatial` (Exact)
- **DC definition:** "Spatial characteristics of the resource."
- **DC recommended usage:** `spatial` is a subproperty of `coverage`. The usage note for `coverage` says: "Spatial topic and spatial applicability may be a named place or a location specified by its geographic coordinates. … Recommended practice is to use a controlled vocabulary such as the Getty Thesaurus of Geographic Names [TGN]. Where appropriate, named places or time periods may be used in preference to numeric identifiers such as sets of coordinates or date ranges."
- **DC example:** `Blacksburg (Va.)` (or the matching Getty TGN URI)
- **Our value:** `Europe,Belgium , West Flanders ,Heuvelland , Wijtschate` (DH80_S004)

### `location` → `dcterms:spatial` (Close, coordinates)
- **DC definition / recommended usage:** same as `spatial`. DCMI's Point encoding scheme writes coordinates as `east=…; north=…`.
- **DC example:** `east=2.8658; north=50.7874`
- **Our value:** `50.7874||2.8658` (DH80_S004)
- **Notes:** We store coordinates as two values, latitude then longitude. DCMI Point writes them as one string, east (longitude) first.

## Topic

### `subject` → `dcterms:subject` (Exact)
- **DC definition:** "A topic of the resource."
- **DC recommended usage:** "Recommended practice is to refer to the subject with a URI. If this is not possible or feasible, a literal value that identifies the subject may be provided. Both should ideally refer to a value in a controlled vocabulary."
- **DC example:** `Virginia Tech Shootings, Blacksburg, Va., 2007` (illustrative; use the real LCSH heading or its id.loc.gov URI)
- **Our value:** `Virginia Tech shootings||April 16, 2007` (Ms2008-020)

### `tags` → `dcterms:subject` (Close)
- **DC definition / recommended usage:** same as `subject`. DC has no separate property for uncontrolled keywords.
- **DC example:** `painting||eggs||art`
- **Our value:** `Virginia Tech shootings||April 16, 2007||April 16||2007||painting||eggs||art` (Ms2008-020)
- **Notes:** These are free-text keywords. A DC export would add them to `subject`, separate from the controlled headings.

## Related resources

### `relation` → `dcterms:relation` (Exact)
- **DC definition:** "A related resource."
- **DC recommended usage:** "Recommended practice is to identify the related resource by means of a URI. If this is not possible or feasible, a string conforming to a formal identification system may be provided."
- **DC example:** `https://example.edu/finding-aids/edwards-family`
- **Our value:** `Edwards Family Collection [1942-1953]. Christiansburg Institute Museum & Archives. Christiansburg, VA.` (CIDA_JFC)

### `related_url` → `dcterms:relation` (Close)
- **DC definition / recommended usage:** same as `relation`. This field fits the URI form DCMI recommends. (`dcterms:references` could also work if the collection itself cites the page.)
- **DC example:** `https://www.example.edu/related-exhibit`
- **Our value:** `https://liberalarts.vt.edu/research-centers/center-for-humanities.html` (69938782)

### `source` → `dcterms:source` (Exact)
- **DC definition:** "A related resource from which the described resource is derived."
- **DC recommended usage:** "This property is intended to be used with non-literal values. The described resource may be derived from the related resource in whole or in part. Best practice is to identify the related resource by means of a URI or a string conforming to a formal identification system."
- **DC example:** `https://example.edu/finding-aids/april-16` (finding aid URL)
- **Our value:** `See the finding aid for the April 16 Collection` (Ms2008-020)
- **Notes:** DCMI would want the finding aid's URL here, not a sentence about it.

---

## Accepted by ingest, not yet used

No record in the vtdlppprd `Collection` table has any of these fields, so there's no "Our value". Where the site's field reference (`metadataFieldInfo.json`) has an example, it's shown as **Site reference example**.

### Names and identifiers

#### `alternative` → `dcterms:alternative` (Exact)
- **DC definition:** "An alternative name for the resource."
- **DC recommended usage:** "The distinction between titles and alternative titles is application-specific."
- **DC example:** `April 16 Eggs`
- **Site reference example:** `Adult teeth clacker; url: https://digital.lib.vt.edu/archive/77af7ceb`

#### `contributor` → `dcterms:contributor` (Exact)
- **DC definition:** "An entity responsible for making contributions to the resource."
- **DC recommended usage:** "The guidelines for using names of persons or organizations as creators apply to contributors." In other words: use a URI if you can, otherwise a name.
- **DC example:** `Virginia Tech. University Libraries`
- **Site reference example:** `Virginia-Maryland College of Veterinary Medicine`

#### `publisher` → `dcterms:publisher` (Exact)
- **DC definition:** "An entity responsible for making the resource available."
- **DC recommended usage:** No comment from DCMI.
- **DC example:** `Virginia Tech University Libraries`
- **Site reference example:** `United States Department of the Interior Geological Survey`
- **Notes:** This overlaps with `repository`, which I mapped loosely to `publisher` above. A collection that fills in both would export two `publisher` values.

#### `other_identifier` → `dcterms:identifier` (Close)
- **DC definition:** "An unambiguous reference to the resource within a given context."
- **DC recommended usage:** "Recommended practice is to identify the resource by means of a string conforming to an identification system."
- **DC example:** `OCLC: 123456789`
- **Site reference example:** `Occurrence ID: 565cbc5e-1449-484c-9841-d5d6689ad2bc|| Record ID: 565cbc5e-1449-484c-9841-d5d6689ad2bc`
- **Notes:** DC allows `identifier` to repeat, so these would be extra `identifier` values next to the main one.

### Dates and coverage

#### `created` → `dcterms:created` (Exact)
- **DC definition:** "Date of creation of the resource."
- **DC recommended usage:** "Recommended practice is to describe the date, date/time, or period of time as recommended for the property Date, of which this is a subproperty." (That means ISO 8601.)
- **DC example:** `1941-03-25`
- **Site reference example:** `3/25/1941`
- **Notes:** This is separate from `create_date`, which holds a single value and looks like a record timestamp in our data. `created` holds multiple values and is the better fit for when the material was made. The site's example isn't in ISO 8601 format.

#### `circa` → `dcterms:date` (Loose)
- **DC definition:** "A point or period of time associated with an event in the lifecycle of the resource."
- **DC recommended usage:** DC has no "approximate" flag. Of the formats DCMI recommends, EDTF can mark a date as approximate with `~`.
- **DC example:** `1950~`
- **Site reference example:** none. The access site lists `circa` as a display field but doesn't document it.

#### `temporal` → `dcterms:temporal` (Exact)
- **DC definition:** "Temporal characteristics of the resource."
- **DC recommended usage:** No comment from DCMI. As with `coverage`, a named period is preferred over a numeric range "where appropriate".
- **DC example:** `World War, 1914-1918` or `1900/1950`
- **Site reference example:** `1900-1950`

#### `coverage` → `dcterms:coverage` (Exact)
- **DC definition:** "The spatial or temporal topic of the resource, spatial applicability of the resource, or jurisdiction under which the resource is relevant."
- **DC recommended usage:** "Spatial topic and spatial applicability may be a named place or a location specified by its geographic coordinates. Temporal topic may be a named period, date, or date range. A jurisdiction may be a named administrative entity or a geographic place to which the resource applies. Recommended practice is to use a controlled vocabulary such as the Getty Thesaurus of Geographic Names [TGN]. Where appropriate, named places or time periods may be used in preference to numeric identifiers such as sets of coordinates or date ranges."
- **DC example:** `Abingdon (Va.)`
- **Site reference example:** `Abingdon, Washington, Virginia, United States`
- **Notes:** `spatial` and `temporal` are more specific versions of `coverage`. Use those when you know which kind of coverage it is.

### Physical and technical

#### `medium` → `dcterms:medium` (Exact)
- **DC definition:** "The material or physical carrier of the resource."
- **DC recommended usage:** No comment from DCMI. A controlled vocabulary such as the Getty AAT is common practice.
- **DC example:** `oil on canvas` or `newspapers`
- **Site reference example:** `newspapers`

#### `resource_type` → `dcterms:type` (Close)
- **DC definition:** "The nature or genre of the resource."
- **DC recommended usage:** "Recommended practice is to use a controlled vocabulary such as the DCMI Type Vocabulary [DCMI-TYPE]. To describe the file format, physical medium, or dimensions of the resource, use the property Format."
- **DC example:** `Collection`
- **Site reference example:** none. The site doesn't document `resource_type`, and it isn't clear how it differs from `type`.

#### `conforms_to` → `dcterms:conformsTo` (Exact)
- **DC definition:** "An established standard to which the described resource conforms."
- **DC recommended usage:** No comment from DCMI. Usually a URI for the standard.
- **DC example:** `https://iiif.io/api/presentation/3/`
- **Site reference example:** `https://iiif.io/api/presentation/3/`

### Rights and access

#### `license` → `dcterms:license` (Exact)
- **DC definition:** "A legal document giving official permission to do something with the resource."
- **DC recommended usage:** "Recommended practice is to identify the license document with a URI. If this is not possible or feasible, a literal value that identifies the license may be provided."
- **DC example:** `https://creativecommons.org/licenses/by-nc/4.0/`
- **Site reference example:** `http://creativecommons.org/publicdomain/zero/1.0/`

#### `embargo_note` → `dcterms:accessRights` (Close)
- **DC definition:** "Information about who access the resource or an indication of its security status."
- **DC recommended usage:** "Access Rights may include information regarding access or restrictions based on privacy, security, or other policies."
- **DC example:** `Restricted until 2027-12-04 at the request of the donor.`
- **Site reference example:** `Restricted by the collection manager until embargo end date`
- **Notes:** The ingest also saves a CSV column named `note` as `embargo_note`.

#### `explicit` → `dcterms:audience` (Loose)
- **DC definition:** "A class of agents for whom the resource is intended or useful."
- **DC recommended usage:** "Recommended practice is to use this property with non-literal values from a vocabulary of audience types."
- **DC example:** `Adults`
- **Site reference example:** `True/False`
- **Notes:** The ingest treats `explicit` as true/false like `explicit_content`, but saves it under the name `explicit`. The Collection API only returns `explicit_content`, so collection CSVs should use `explicit_content`.

### Relationships

#### `is_part_of` → `dcterms:isPartOf` (Exact)
- **DC definition:** "A related resource in which the described resource is physically or logically included."
- **DC recommended usage:** "This property is intended to be used with non-literal values. This property is an inverse property of Has Part."
- **DC example:** `https://example.edu/collection/Ms1990-057`
- **Site reference example:** `Ms1990-057`
- **Notes:** This is free text. It does **not** place the collection under a parent the way `parent_collection_identifier` does.

#### `belongs_to` → `dcterms:isPartOf` (Loose)
- **DC definition / recommended usage:** same as `is_part_of`.
- **DC example:** `https://example.edu/collection/Ms1990-057`
- **Site reference example:** none. The site lists `belongs_to` as a display field but doesn't document it.

#### `has_part` → `dcterms:hasPart` (Exact)
- **DC definition:** "A related resource that is included either physically or logically in the described resource."
- **DC recommended usage:** "This property is intended to be used with non-literal values. This property is an inverse property of Is Part Of."
- **DC example:** `https://example.edu/collection/Ms1990-057-series-1`
- **Site reference example:** `Chapter 1`

#### `has_format` → `dcterms:hasFormat` (Exact)
- **DC definition:** "A related resource that is substantially the same as the pre-existing described resource, but in another format."
- **DC recommended usage:** "This property is intended to be used with non-literal values. This property is an inverse property of Is Format Of."
- **DC example:** `https://example.edu/finding-aids/ms1990-057.pdf`
- **Site reference example:** `https://digital.lib.vt.edu/archive/s253n52s`

#### `has_version` → `dcterms:hasVersion` (Exact)
- **DC definition:** "A related resource that is a version, edition, or adaptation of the described resource."
- **DC recommended usage:** "Changes in version imply substantive changes in content rather than differences in format. This property is intended to be used with non-literal values. This property is an inverse property of Is Version Of."
- **DC example:** `https://example.edu/collection/vtac-2024-edition`
- **Site reference example:** `First edition`

#### `is_version_of` → `dcterms:isVersionOf` (Exact)
- **DC definition:** "A related resource of which the described resource is a version, edition, or adaptation."
- **DC recommended usage:** "Changes in version imply substantive changes in content rather than differences in format. This property is intended to be used with non-literal values. This property is an inverse property of Has Version."
- **DC example:** `https://example.edu/collection/vtac`
- **Site reference example:** `Folder 11 || Pardy Residence`

#### `references` → `dcterms:references` (Exact)
- **DC definition:** "A related resource that is referenced, cited, or otherwise pointed to by the described resource."
- **DC recommended usage:** "This property is intended to be used with non-literal values. This property is an inverse property of Is Referenced By."
- **DC example:** `https://example.edu/exhibits/april-16`
- **Site reference example:** `https://ecdysis.org/collections/individual/index.php?occid=1730992`

#### `provider` → `dcterms:publisher` (Loose)
- **DC definition:** "An entity responsible for making the resource available."
- **DC recommended usage:** No comment from DCMI.
- **DC example:** `Virginia Tech University Libraries`
- **Site reference example:** none.
- **Notes:** This matches Europeana's `edm:provider` (the aggregator that supplies the data). The old Amplify Collection schema has this field; the new CDK schema doesn't.

### Accessibility

#### `alt_text` → `dcterms:description` (Loose)
- **DC definition:** "An account of the resource."
- **DC recommended usage:** "Description may include but is not limited to: an abstract, a table of contents, a graphical representation, or a free-text account of the resource."
- **DC example:** `Painted egg decorated with orange and maroon stripes`
- **Site reference example:** `page1: Detail of barn structure`
- **Notes:** DC has no accessibility properties. This is short screen-reader text for an image. On a collection it will be used for the thumbnail's alt text.

### Site and ingest controls

#### `title_template` → no DC equivalent (None)
- **DC definition / usage:** —
- **Site reference example:** `Special Collections and University Archives, Virginia Tech.`
- **Notes:** This is a display setting. The site fills in this template to build page titles (`SiteTitle.tsx`, default `{{title}}`).

#### `filename` → no DC equivalent (None)
- **DC definition / usage:** —
- **Notes:** This column is only an input to the ingest and is never saved itself. For a `.pdf` or `.jpg` name, the ingest builds `thumbnail_path` and `manifest_url` from it. For a `video.vt.edu/media` link, it builds `thumbnail_path` and stores the link as `manifest_url`. On a collection, that replaces the default thumbnail path.
