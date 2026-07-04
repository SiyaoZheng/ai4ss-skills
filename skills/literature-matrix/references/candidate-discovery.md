# Candidate Discovery

Use this reference when the researcher has an open-ended topic or needs current literature coverage. The goal is to avoid a polished empty matrix: first make the source search itself inspectable.

## Discovery Package

Produce `.aiss source-discovery declarations` before extraction when sources are not already fixed.

Required columns:

| column | meaning |
|---|---|
| `route_id` | Route/design id this literature search serves |
| `design_source` | Path to the design brief or MIDA declaration |
| `target_inquiry` | Estimand, descriptive quantity, measurement target, classification target, process-tracing claim, or synthesis question |
| `candidate_id` | Stable short id |
| `search_stratum` | concept, method, outcome, setting, anchor_author, backward_chase, forward_chase, database_refresh |
| `query_or_seed` | Exact query string, seed paper, author, DOI, or local path |
| `title` | Candidate title or `unknown_title` |
| `authors` | Candidate authors or `unknown_authors` |
| `year` | Source year, version year, or `unknown_year` |
| `source_type` | journal_page, doi_record, working_paper_repository, author_page, local_pdf, citation_index, policy_report, secondary_pointer |
| `source_url_or_path` | URL, DOI, local path, or database record |
| `source_status` | ready_for_extraction, needs_primary_source, needs_pdf, needs_version_check, background_only, duplicate_candidate, excluded, unverified |
| `reason` | Why the item is in or out |
| `next_action` | retrieve_pdf, open_primary_page, check_doi, deduplicate, extract_matrix_row, exclude, ask_author |
| `relevance_axis` | Project-specific axis or generic axis: concept, mechanism, boundary_condition, rival_explanation, observable_implication, method_anchor, measurement, other |
| `found_from` | Search engine, database, seed paper, Zotero, local ref, or citation chasing source |
| `access_date` | YYYY-MM-DD |

## Minimum Search Coverage

For an open-ended empirical topic, include at least:

- 3 concept/outcome query strata.
- 1 method query stratum when a design family matters.
- 1 setting or language stratum when geography matters.
- 3-5 seed sources with stable pages or local PDFs.
- 2 backward-chase or forward-chase targets from verified seed sources, when available.
- A separate `background_only` path for policy reports, measurement papers, and conceptual pieces.

## Source-Status Standards

- `ready_for_extraction`: primary or local source is available and the row can enter the matrix.
- `needs_primary_source`: only a search result, citation index, abstracting service, or secondary pointer has been found.
- `needs_pdf`: primary page exists but the methods/results cannot yet be checked.
- `needs_version_check`: working paper, preprint, or publication status may have changed.
- `background_only`: useful for context or measurement, not causal evidence.
- `duplicate_candidate`: likely same paper as another row; keep until deduped.
- `excluded`: outside scope; preserve reason.
- `unverified`: no stable source or metadata conflict.

## Seed Source Audit

For each seed source, record:

- why it is a seed, not just a keyword hit;
- whether it is primary, local, or secondary;
- which evidence axis it covers;
- what citation chasing it enables;
- what author decision it forces.

Good seed sources cover different roles: main empirical design, adjacent outcome, mechanism, method warning, measurement/background.

## Snowballing

Use backward chasing for references cited by verified seed papers. Use forward chasing for papers that cite the seed paper. Keep these as candidate rows until verified.

Do not treat a citation count, search rank, or related-articles result as evidence. It is only a pointer to candidate sources.

## Hand-Off To Matrix

Only candidates with `source_status=ready_for_extraction` can become matrix rows with `included_in_synthesis=true`. Rows marked `needs_primary_source`, `needs_pdf`, `needs_version_check`, or `unverified` may appear in a pending-source tab, but not as support for a literature claim.

## Method References

- PRISMA 2020 checklist for transparent search, screening, and inclusion reporting: <https://www.prisma-statement.org/prisma-2020-checklist>.
- Wohlin 2014 on backward and forward snowballing in systematic literature studies: <https://doi.org/10.1145/2601248.2601268>.
