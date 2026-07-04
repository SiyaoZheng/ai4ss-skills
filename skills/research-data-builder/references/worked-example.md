# Worked Example: City-Year Policy Panel

This example is designed for AI4SS classroom demonstrations.

## Scenario

Research question: whether a city-level policy pilot affects firm innovation.

Unit: `city_id x year`

Period: 2012-2023

Inputs:

| path | role | key columns |
|---|---|---|
| `data/raw/patents_city_year.csv` | outcome | `city_code`, `year`, `patent_count` |
| `data/raw/policy_pilots.xlsx` | treatment timing | `city_name`, `first_policy_year` |
| `data/raw/city_controls.csv` | controls | `city_id`, `year`, `gdp_pc`, `population`, `fiscal_revenue` |
| `docs/city_crosswalk.csv` | city name/id map | `city_name`, `city_id`, `city_code` |

Target output:

`data/analysis/city_panel_analysis.csv`

## Stage Plan

| stage | script | output | validation |
|---|---|---|---|
| ingest | `scripts/10_ingest_city_sources.R` | `data/interim/source_inventory.csv` | file existence, column names |
| harmonize | `scripts/20_harmonize_city_ids.R` | `data/interim/city_sources_harmonized.csv` | duplicate key check |
| merge | `scripts/30_merge_city_panel.R` | `data/interim/city_panel_merged.csv` | merge audit |
| construct | `scripts/40_construct_variables.R` | `data/analysis/city_panel_analysis.csv` | variable provenance |
| audit | `scripts/50_audit_analysis_sample.R` | `output/audit/sample_flow.csv` | sample flow and missingness |

## Good Agent Trace

```text
Plan:
1. Inspect AGENTS.md and variable dictionary.
2. Check whether city_id-year is unique in each source.
3. Build crosswalk before merging.
4. Merge outcomes, treatment timing, and controls.
5. Construct post and did after treatment timing is verified.
6. Write sample_flow, merge_audit, and variable_provenance.
```

Tool actions should show file reads, column inspection, duplicate checks, script edits, and reruns. A single "here is the cleaned data" answer is insufficient.

## Example Audit Rows

`sample_flow.csv`

| step | input_path | output_path | n_before | n_after | units_before | units_after | years_before | years_after | reason | check_status | notes |
|---|---|---|---:|---:|---:|---:|---|---|---|---|---|
| raw_patents | data/raw/patents_city_year.csv | data/interim/patents_city_year.csv | 3420 | 3420 | 285 | 285 | 2012-2023 | 2012-2023 | read source | pass | no row loss |
| drop_missing_outcome | data/interim/city_panel_merged.csv | data/analysis/city_panel_analysis.csv | 3420 | 3388 | 285 | 285 | 2012-2023 | 2012-2023 | 32 city-years lack patent_count | warn | review missingness |

`merge_audit.csv`

| merge_name | left_path | right_path | keys | left_rows | right_rows | matched_rows | left_only_rows | right_only_rows | duplicate_key_rows | action | review_path |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| city_crosswalk | data/raw/patents_city_year.csv | docs/city_crosswalk.csv | city_code | 3420 | 285 | 3420 | 0 | 3 | 0 | review | output/audit/unused_city_names.csv |
| policy_timing | data/interim/patents_harmonized.csv | data/raw/policy_pilots.xlsx | city_id | 3420 | 265 | 240 | 3180 | 0 | 0 | keep | output/audit/never_treated_cities.csv |
| controls | data/interim/city_policy_panel.csv | data/raw/city_controls.csv | city_id;year | 3420 | 3440 | 3310 | 78 | 120 | 0 | repair | output/audit/missing_controls.csv |

`variable_provenance.csv`

| variable | source_variables | rule | script_path | validation | status |
|---|---|---|---|---|---|
| `ln_patent` | `patent_count` | `log(1 + patent_count)` | scripts/40_construct_variables.R | range and zero check | ready |
| `post` | `year`; `first_policy_year` | `year >= first_policy_year` for treated cities | scripts/40_construct_variables.R | timing cross-tab | ready |
| `did` | `treat_city`; `post` | product of treatment group and post | scripts/40_construct_variables.R | treated-post count | ready |

## Stop Conditions

Stop the workflow if:

- `city_id x year` is not unique after a merge.
- Treatment timing is missing for treated cities.
- Outcome data use city names that cannot be crosswalked.
- Low-confidence text extraction is needed for a core variable.
- Final sample drops more than 10% of treated observations without explanation.

## Classroom Debrief

What students should notice:

- The agent does not start by writing a regression.
- The agent creates audit artifacts that survive outside the chat.
- The researcher still decides whether unmatched cities or missing controls are substantively acceptable.
