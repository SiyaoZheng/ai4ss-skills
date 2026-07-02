# Study Design Declaration Schema

Use `study_design_declaration.csv` when a selected route becomes a reusable design source. This sidecar is the hard MIDA declaration.

## Required Columns

| column | meaning |
|---|---|
| `declaration_id` | Stable id such as `M1` |
| `route_id` | Route from `research_route_cards.csv` |
| `study_type` | `descriptive`, `causal`, `prediction`, `text_analysis`, `case_comparison`, `qualitative`, `mixed_methods`, or `theory_mapping` |
| `mida_component` | `model`, `inquiry`, `data_strategy`, `answer_strategy`, `diagnose`, `redesign`, or `report_boundary` |
| `declaration_text` | The declared content for this component |
| `declaration_source` | `author_supplied`, `material_inferred`, `literature_inferred`, `agent_proposed`, or `unresolved` |
| `status` | `declared`, `needs_author_decision`, `needs_data_check`, `needs_literature_check`, `needs_methods_review`, or `blocked` |
| `evidence_source` | File, note, source row, data preview, or `not_applicable:<reason>` |
| `diagnosand_or_gate` | What would be checked before claims depend on this component |
| `redesign_option` | Smaller route, revised measure, added source, changed comparison, changed estimator, or abandon condition |
| `interpretation_boundary` | What this design element can and cannot support |
| `author_decision_needed` | Researcher decision or `not_applicable:<reason>` |
| `ai4ss_model_path` | Path to `.aiss` model, or `not_applicable:<reason>` |
| `model_id` | DSL model id touched by this row, or `not_applicable:<reason>` |
| `concept_id` | DSL concept id touched by this row, or `not_applicable:<reason>` |
| `causal_id` | DSL causal implication id touched by this row, or `not_applicable:<reason>` |
| `bridge_id` | DSL empirical bridge id touched by this row, or `not_applicable:<reason>` |
| `ai4ss_check_status` | `pass`, `warn`, `fail`, `not_run`, or `not_applicable` |
| `commensurability_status` | `strong`, `weak`, `unchecked`, `mixed`, or `not_applicable` |
| `next_skill_route` | `research-data-builder`, `literature-matrix`, `research-analysis-runner`, `methods-reviewer`, `did-expert`, `ask_author`, or `none` |

## Rules

- Each `route_id` must have exactly one row for every required MIDA component.
- `inquiry` must name the target estimand, descriptive quantity, measurement target, classification target, process-tracing claim, or synthesis question.
- Causal designs must state a target comparison, outcome, exposure/treatment, population or unit, and time window or scale in the `inquiry` row.
- `data_strategy` must name source selection, measurement, extraction, linkage, missingness, or sampling rules.
- `answer_strategy` must name the estimator, coding rule, synthesis rule, diagnostic comparison, or output procedure.
- `diagnose` must have a concrete `diagnosand_or_gate`.
- `redesign` must have a concrete `redesign_option`.
- `report_boundary` must have a concrete `interpretation_boundary`.
- If `ai4ss_model_path` is not `not_applicable:<reason>`, it must end with `.aiss`.
- If `study_type` is `causal`, `theory_mapping`, `mixed_methods`, or construct-heavy qualitative work, the row set should either point to `research_model.aiss` or state why a DSL model is not applicable.
- `ai4ss_check_status=fail` is not a valid ready handoff.
- Causal or measurement rows with a `causal_id` or `bridge_id` must declare `commensurability_status` rather than leaving it implicit.
- Rows with `needs_author_decision` route to `ask_author`.
- Rows with `needs_data_check` route to `research-data-builder`.
- Rows with `needs_literature_check` route to `literature-matrix`.
- Rows with `needs_methods_review` route to `methods-reviewer` or `did-expert`.
