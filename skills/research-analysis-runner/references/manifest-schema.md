# Analysis Run Manifest Schema

Use `.aiss analysis artifact declarations` to make first-pass analysis outputs reviewable.

## Required Columns

| column | meaning |
|---|---|
| `run_id` | Stable id such as `A1` |
| `route_id` | Route from starter/design artifacts |
| `design_source` | Path to design brief or analysis plan |
| `target_inquiry` | Estimand, descriptive quantity, measurement target, classification target, process-tracing claim, or synthesis question |
| `data_source` | Path to analysis-ready data or source output |
| `script_path` | Script/notebook that produced the output |
| `output_path` | Table, figure, model object, coded output, or log path |
| `output_type` | `table`, `figure`, `model`, `coded_data`, `log`, or `diagnostic` |
| `model_or_operation` | Formula, operation name, or coding action |
| `sample_note` | Unit, period, sample restrictions, or source slice |
| `readiness_check_path` | Path to `.aiss readiness checks` used before execution |
| `readiness_status` | `ready`, `warn`, or `blocked` status from the readiness gate |
| `status` | `ready_for_review`, `needs_review`, `warning`, or `blocked` |
| `validation_command` | Command run or `not_run_reason:<reason>` |
| `interpretation_boundary` | What the output can and cannot support |
| `ai4ss_model_path` | Path to `.aiss` model, or `not_applicable:<reason>` |
| `model_id` | DSL model id served by this output, or `not_applicable:<reason>` |
| `concept_id` | DSL concept id served by this output, or `not_applicable:<reason>` |
| `causal_id` | DSL causal implication id served by this output, or `not_applicable:<reason>` |
| `bridge_id` | DSL empirical bridge id served by this output, or `not_applicable:<reason>` |
| `ai4ss_check_status` | `pass`, `warn`, `not_run`, or `not_applicable` |
| `next_skill_route` | `methods-reviewer`, `academic-writing-scaffold`, `research-slides-builder`, `study-design-builder`, `research-data-builder`, `ask_author`, or `none` |

## Rules

- Final handoff should use `ready_for_review` or `needs_review`, not `blocked`.
- `blocked` requires a `not_run_reason:<reason>` validation command.
- Results that affect claims should route to `methods-reviewer`.
- `academic-writing-scaffold` should only appear after author approval or methods review.
- `interpretation_boundary` cannot be blank or `none`.
- `target_inquiry` must match the upstream design source.
- `readiness_check_path` must point to the gate that validated clean data against the analysis plan.
- `ready_for_review` outputs cannot have `readiness_status=blocked`.
- `ai4ss_model_path` must end with `.aiss` unless it is `not_applicable:<reason>`.
- Outputs tied to a model-linked causal claim should fill `causal_id` or `bridge_id`.
- `ai4ss_check_status=fail` is not a valid final handoff.
