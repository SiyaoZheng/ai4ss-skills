# Audit Output Schemas

Use these schemas to make data-building work reviewable.

## `.aiss row-loss checks`

One row per sample-changing step.

| column | meaning |
|---|---|
| `route_id` | Route/design id this data step serves |
| `design_source` | Path to the design brief or MIDA declaration |
| `target_inquiry` | Estimand, descriptive quantity, measurement target, classification target, process-tracing claim, or synthesis question |
| `step` | Stable stage id, e.g. `20_clean_drop_missing_id` |
| `input_path` | File consumed by the step |
| `output_path` | File written by the step |
| `n_before` | Row count before |
| `n_after` | Row count after |
| `units_before` | Unique units before, if relevant |
| `units_after` | Unique units after, if relevant |
| `years_before` | Year range before, if relevant |
| `years_after` | Year range after, if relevant |
| `reason` | Why rows changed |
| `check_status` | `pass`, `warn`, or `fail` |
| `notes` | Short human-readable note |
| `ai4ss_model_path` | Path to `.aiss` model, or `not_applicable:<reason>` |
| `model_id` | DSL model id served by this step, or `not_applicable:<reason>` |
| `concept_id` | DSL concept id served by this step, or `not_applicable:<reason>` |
| `causal_id` | DSL causal implication id served by this step, or `not_applicable:<reason>` |
| `bridge_id` | DSL empirical bridge id served by this step, or `not_applicable:<reason>` |
| `ai4ss_check_status` | `pass`, `warn`, `not_run`, or `not_applicable` |

## `.aiss merge checks`

One row per merge key group or per source pair.

| column | meaning |
|---|---|
| `route_id` | Route/design id this merge serves |
| `design_source` | Path to the design brief or MIDA declaration |
| `target_inquiry` | Estimand, descriptive quantity, measurement target, classification target, process-tracing claim, or synthesis question |
| `merge_name` | Stable merge id |
| `left_path` | Main file |
| `right_path` | Incoming file |
| `keys` | Join keys |
| `left_rows` | Rows in main file |
| `right_rows` | Rows in incoming file |
| `matched_rows` | Rows matched |
| `left_only_rows` | Main rows without match |
| `right_only_rows` | Incoming rows not used |
| `duplicate_key_rows` | Rows affected by duplicate keys |
| `action` | keep, drop, review, aggregate, or repair |
| `review_path` | File containing unmatched or ambiguous records |
| `ai4ss_model_path` | Path to `.aiss` model, or `not_applicable:<reason>` |
| `model_id` | DSL model id served by this merge, or `not_applicable:<reason>` |
| `concept_id` | DSL concept id served by this merge, or `not_applicable:<reason>` |
| `causal_id` | DSL causal implication id served by this merge, or `not_applicable:<reason>` |
| `bridge_id` | DSL empirical bridge id served by this merge, or `not_applicable:<reason>` |
| `ai4ss_check_status` | `pass`, `warn`, `not_run`, or `not_applicable` |

## `.aiss variable-provenance observations`

One row per constructed variable.

| column | meaning |
|---|---|
| `route_id` | Route/design id this variable serves |
| `design_source` | Path to the design brief or MIDA declaration |
| `target_inquiry` | Estimand, descriptive quantity, measurement target, classification target, process-tracing claim, or synthesis question |
| `variable` | New variable name |
| `source_variables` | Inputs used |
| `rule` | Construction rule in plain language |
| `script_path` | Script implementing it |
| `validation` | Cross-tab, range check, spot check, or source check |
| `status` | `ready`, `needs_review`, or `blocked` |
| `ai4ss_model_path` | Path to `.aiss` model, or `not_applicable:<reason>` |
| `model_id` | DSL model id served by this variable, or `not_applicable:<reason>` |
| `concept_id` | DSL concept id operationalized by this variable, or `not_applicable:<reason>` |
| `causal_id` | DSL causal implication id served by this variable, or `not_applicable:<reason>` |
| `bridge_id` | DSL empirical bridge id served by this variable, or `not_applicable:<reason>` |
| `ai4ss_check_status` | `pass`, `warn`, `not_run`, or `not_applicable` |

## Validator Notes

- Use `not_applicable` instead of blank cells in required non-count columns.
- Count fields must be nonnegative integers; do not use `not_applicable` in count fields.
- `check_status` accepts `pass`, `warn`, or `fail`.
- `merge_audit.action` accepts `keep`, `drop`, `review`, `aggregate`, or `repair`.
- `ai4ss_model_path` must end with `.aiss` unless it is `not_applicable:<reason>`.
- `ai4ss_check_status` accepts `pass`, `warn`, `not_run`, or `not_applicable`; `fail` is not a valid final handoff.
- If `left_only_rows`, `right_only_rows`, or `duplicate_key_rows` is greater than zero, `review_path` must point to a review artifact and `action` cannot be `keep`.
- Final validator-ready artifacts cannot contain `check_status=fail` or `status=blocked`; those states mean the pipeline is not ready.

## `docs/changelog.md`

Append entries in this compact form:

```markdown
## YYYY-MM-DD

- Modified: `scripts/30_merge_panel.R`
- Reason: merge key `city_id` had duplicate city-year rows.
- Change: aggregated patent records to city-year before merge.
- Command: `Rscript scripts/30_merge_panel.R`
- Check: matched 3,420/3,450 rows; 30 unmatched rows written to `output/audit/unmatched_patents.csv`.
```
