# Worked Example: Place-Based Policy And Innovation

This example is for teaching evidence-matrix construction, not for making a substantive claim about the actual literature without live verification.

## User Task

```text
Build `.aiss` source-evidence declarations for empirical studies on place-based policy and innovation.
Focus on papers that identify effects using DID, event studies, RD, IV, or synthetic-control designs.
Do not write review prose.
```

## Search Strata

| stratum | example query | purpose |
|---|---|---|
| core concept | `"place-based policy" innovation patents` | broad candidate set |
| policy pilot | `"policy pilot" city innovation patents DID` | China-style pilot designs |
| method | `"enterprise zone" patents "difference-in-differences"` | design-specific retrieval |
| mechanism | `"R&D" "place-based" policy firms` | channel evidence |
| anchor chase | papers citing known anchor studies | coverage and genealogy |

## Candidate Discovery Rows

Before extraction, create `.aiss source-discovery declarations`.

| candidate_id | search_stratum | source_type | source_status | next_action | why it matters |
|---|---|---|---|---|---|
| `anchor_place_policy` | `anchor_author` | `journal_page` | `ready_for_extraction` | `extract_matrix_row` | verified seed for place-based policy design |
| `pilot_policy_query_01` | `concept` | `citation_index` | `needs_primary_source` | `open_primary_page` | keyword hit; not evidence yet |
| `innovation_measurement_report` | `outcome` | `policy_report` | `background_only` | `ask_author` | measurement context, not causal evidence |
| `anchor_forward_01` | `forward_chase` | `citation_index` | `needs_primary_source` | `open_primary_page` | citation-chasing target from verified seed |

## Screening Decisions

| candidate | status | reason |
|---|---|---|
| Paper A | include | studies policy exposure and innovation outcome with empirical design |
| Paper B | maybe | studies firm productivity, innovation secondary |
| Paper C | exclude | theoretical model only |
| Paper D | duplicate | working paper and journal article are same paper |
| Paper E | unverified | search snippet only; no stable source |

## Source-Evidence Declaration Example

| column | example value |
|---|---|
| `paper_id` | `author_year_place_innovation` |
| `citation` | `Author Year, Place-based policy and innovation` |
| `authors` | `Author A; Author B` |
| `year` | `2024` |
| `status` | `working_paper` |
| `venue_or_series` | `official working-paper series` |
| `doi` | `no_doi: working paper` |
| `url` | `https://example.edu/papers/place-policy-innovation` |
| `verification_level` | `verified_local` |
| `research_question` | `whether place-based policy exposure changes innovation outcomes` |
| `setting_sample` | `city-year or firm-year panel, period visible in source` |
| `treatment_or_exposure` | `policy designation / zone eligibility / pilot adoption` |
| `data_sources` | `patent records; policy-designation list; city controls` |
| `outcomes` | `patents, R&D, firm entry, productivity` |
| `identification_strategy` | `DID/event study; details verified from methods section` |
| `fixed_effects_controls` | `city and year fixed effects; controls visible in table note` |
| `validation_checks` | `pre-trends, placebo timing, alternative controls when visible` |
| `main_findings` | `neutral direction and scope, tied to source` |
| `claim_source_section` | `table_figure` |
| `claim_source_locator` | `Table 2; Figure 3` |
| `limitations` | `spillovers and treatment timing remain open concerns` |
| `relevance_to_project` | `helps benchmark city-level innovation policy designs` |
| `open_questions` | `external validity, treatment timing, spillovers` |
| `verified_from` | `ref/papers/author_year_place_innovation.pdf` |
| `access_date` | `2026-06-25` |
| `version_used` | `local PDF dated 2024-10` |
| `included_in_synthesis` | `true` |

## Evidence Clusters

Cluster types:

1. Policy-zone studies measuring innovation outcomes.
2. Pilot-policy studies using staggered adoption.
3. Firm-level mechanism studies on R&D or entry.
4. Papers showing spillover or displacement concerns.
5. Papers with null or heterogeneous effects.

Each cluster should state:

- what it can support;
- what it cannot support;
- which paper rows are verified;
- which rows still need primary-source checks.

## Classroom Debrief

What students should notice:

- The agent does not jump to "the literature shows".
- Publication status is a variable, not an assumption.
- Method labels are extracted from methods text, not search snippets.
- The output is checked evidence declarations and cluster notes that the researcher uses before writing.
