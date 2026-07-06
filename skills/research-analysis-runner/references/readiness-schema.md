# Analysis Readiness Check Schema

Use `.aiss readiness checks` as the hard gate between cleaned data and
analysis execution. This is the local implementation of the `regression-ready`
stretch idea from `ai4ss-skills`: validate clean data against the declared
analysis plan before any first-pass model, table, or figure is treated as
reviewable.

The gate is still useful for descriptive, text, and qualitative projects. In
those cases, read `regression-ready` as `analysis-ready`: the same .aiss projection checks
whether the available evidence object can answer the declared inquiry.

## Required Columns

| column | meaning |
|---|---|
| `check_id` | Stable id such as `AR1` |
| `route_id` | Route from starter/design artifacts |
| `design_source` | Path to `.aiss MIDA declarations` or design brief |
| `target_inquiry` | Estimand, descriptive quantity, measurement target, classification target, process-tracing claim, or synthesis question |
| `ai4ss_model_path` | Path to `.aiss` model, or `not_applicable:<reason>` |
| `model_id` | DSL model id served by the analysis, or `not_applicable:<reason>` |
| `bridge_id` | DSL empirical bridge id being tested, or `not_applicable:<reason>` |
| `analysis_plan_path` | Path to analysis plan scaffold, preregistration draft, or script plan |
| `data_source` | Path to the cleaned analysis data or extracted evidence table |
| `unit_of_analysis` | Unit/grain expected by the declared inquiry |
| `required_variables` | Semicolon-separated variables required by the analysis plan |
| `available_variables` | Semicolon-separated variables verified in `data_source` or data dictionary |
| `missing_variables` | `none`, or semicolon-separated variables missing from the cleaned data |
| `sample_flow_path` | Path to `.aiss row-loss checks` or `not_applicable:<reason>` |
| `merge_audit_path` | Path to `.aiss merge checks` or `not_applicable:<reason>` |
| `variable_provenance_path` | Path to `.aiss variable-provenance observations` or `not_applicable:<reason>` |
| `row_count` | Number of rows in `data_source` after cleaning |
| `unit_count` | Number of units, or `not_applicable:<reason>` |
| `time_coverage` | Time range, source slice, or `not_applicable:<reason>` |
| `key_integrity_status` | `pass`, `warn`, `fail`, or `not_applicable` |
| `missingness_status` | `pass`, `warn`, `fail`, or `not_applicable` |
| `variation_status` | `pass`, `warn`, `fail`, or `not_applicable` |
| `bridge_alignment_status` | `strong`, `weak`, `mixed`, `unchecked`, `fail`, or `not_applicable` |
| `readiness_status` | `ready`, `warn`, or `repair_needed` |
| `repair_issue` | `none`, or concrete issue that must be repaired before or during execution |
| `validation_command` | Command run or `not_run_reason:<reason>` |
| `next_skill_route` | `research-analysis-runner`, `public-data-sources`, `research-data-builder`, `study-design-builder`, or `methods-reviewer` |

## Rules

- `ready` means the analysis runner may execute the declared first-pass analysis.
- `warn` means execution may proceed only if the warning is explicit and routed
  to review; it cannot silently become a final result.
- `repair_needed` means repair data, design, or methods linkage before treating outputs as reviewable.
- If `ai4ss_model_path` is not `not_applicable:<reason>`, it must end with
  `.aiss`.
- If a `.aiss` model is present, `bridge_alignment_status=unchecked` is not a
  ready handoff.
- `missing_variables` must be `none` for `ready` or `warn` handoffs.
- Any `fail` gate status triggers repair before analysis output is treated as reviewable.
- `ready` rows must route to `research-analysis-runner`.
- `repair_needed` rows route to the skill that can repair the failed gate, then return to `research-analysis-runner`.
- When `data_source` is a readable CSV, the validator checks the real header and
  row count against `required_variables`, `available_variables`,
  `missing_variables`, and `row_count`.
