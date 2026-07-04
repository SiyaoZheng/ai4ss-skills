# Source Verification

Use this reference before treating any paper as evidence.

## Verification Levels

| level | standard | allowed use |
|---|---|---|
| verified_primary | journal page, DOI page, official working-paper page, author PDF, repository record | matrix and evidence clusters |
| verified_local | user-supplied PDF or Zotero item with visible metadata | matrix with local path |
| secondary_only | blog, news, syllabus, search snippet, citation index without source page | pointer only |
| unverified | no stable source or metadata conflict | exclude from evidence table |

## DOI And URL Checks

For each source:

- Open DOI or publisher page when possible.
- Confirm title, authors, year, and version.
- Preserve DOI in canonical form without inventing prefixes.
- If DOI is absent, preserve stable URL and source type.
- Record access date for web-only sources.

## Publication Status

Use conservative labels:

- `journal_article`
- `accepted`
- `working_paper`
- `preprint`
- `conference_paper`
- `book_chapter`
- `report`
- `unverified`

Do not call a working paper peer-reviewed unless the source proves it.

## Claim Verification

For each extracted claim, identify where it came from:

- abstract;
- introduction;
- data section;
- methods section;
- table/figure;
- conclusion;
- appendix;
- secondary summary.

Claims from abstract only must set `claim_source_section` to `abstract_only`.

## Identification Strategy Verification

Do not infer method from keywords. Confirm:

- What creates variation?
- What comparison identifies the estimate?
- What assumptions are stated?
- What fixed effects or controls are used?
- What inference level is used?
- What diagnostics are shown?

If the source says "we use DID" but gives no design details in available text, record `DID claimed; details unavailable`.

## Version Control

For working papers with multiple versions:

- Keep one row for the paper.
- Record `version_used`.
- Put prior titles or series numbers in `version_notes`.
- Prefer the most recent official author/repository version unless the user asks for a published version.

## Red Flags

Mark as `needs_review` when:

- title or author list differs across sources;
- year differs by more than one version cycle;
- publication status is unclear;
- claimed finding appears only in a secondary summary;
- source is a predatory or unclear venue;
- PDF has no title page or metadata.
