# Study Design Declaration Schema

Use `study_design_declaration.csv` when a selected route becomes a reusable design source. In the unified workflow this sidecar mirrors `.aiss` `mida` declarations; the canonical design object is the selected `.aiss` `route` plus seven `.aiss` `mida` rows.

## Required Columns

| column | meaning |
|---|---|
| `declaration_id` | Stable id such as `M1` |
| `mida_id` | Stable `.aiss` MIDA id such as `project.mida_r1_model` |
| `route_id` | Route from `research_route_cards.csv` and matching `.aiss` `route` declaration |
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

- Each selected `.aiss` `route` must have exactly one `mida` declaration, mirrored as one CSV row with a stable `mida_id`, for every required MIDA component.
- `inquiry` must name the target estimand, descriptive quantity, measurement target, classification target, process-tracing claim, or synthesis question.
- Causal designs must state a target comparison, outcome, exposure/treatment, population or unit, and time window or scale in the `inquiry` row.
- `data_strategy` must name source selection, measurement, extraction, linkage, missingness, or sampling rules.
- `answer_strategy` must name the estimator, coding rule, synthesis rule, diagnostic comparison, or output procedure.
- `diagnose` must have a concrete `diagnosand_or_gate`.
- `redesign` must have a concrete `redesign_option`.
- `report_boundary` must have a concrete `interpretation_boundary`.
- If `ai4ss_model_path` is not `not_applicable:<reason>`, it must end with `.aiss` and point to the artifact containing the selected `route` and mirrored `mida` declarations.
- If `study_type` is `causal`, `theory_mapping`, `mixed_methods`, or construct-heavy qualitative work, the row set should either point to `research_model.aiss` or state why a DSL model is not applicable.
- When a `theory_mapping` row depends on `literature_theory_synthesis.csv`, put that sidecar path in `evidence_source` and preserve unresolved novelty, mechanism-strength, or rival-explanation choices in `author_decision_needed` or a `decision` declaration.
- When full theory workbench sidecars are present, reference `literature_theory_synthesis.csv`, `theory_rival_map.csv`, `theory_scope_map.csv`, or `theory_evidence.md` in existing `evidence_source` cells as needed; do not add columns to `study_design_declaration.csv`.
- `ai4ss_check_status=fail` is not a valid ready handoff.
- Causal or measurement rows with a `causal_id` or `bridge_id` must declare `commensurability_status` rather than leaving it implicit.
- Rows with `needs_author_decision` route to `ask_author`.
- Rows with `needs_data_check` route to `research-data-builder`.
- Rows with `needs_literature_check` route to `literature-matrix`.
- Rows with `needs_methods_review` route to `methods-reviewer` or `did-expert`.
