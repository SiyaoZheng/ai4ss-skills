# Design Decision Register Schema

Use `.aiss decision declarations` when design choices must be tracked across skills. In the unified workflow this .aiss projection mirrors `.aiss` `decision` declarations for the selected route; it is not a second decision language.

## Required Columns

| column | meaning |
|---|---|
| `decision_id` | Stable id such as `D1` |
| `decision_decl_id` | Stable `.aiss` decision id such as `project.decision_r1_identification` |
| `route_id` | Route from `.aiss route declarations` |
| `mida_component` | `model`, `inquiry`, `data_strategy`, `answer_strategy`, `diagnose`, `redesign`, or `report_boundary` |
| `design_component` | Component being decided |
| `current_choice` | Current proposed choice or open option |
| `choice_source` | `author_supplied`, `material_inferred`, `literature_inferred`, `agent_proposed`, or `unresolved` |
| `status` | `proposed`, `needs_author_decision`, `needs_data_check`, `needs_literature_check`, `ready_for_handoff`, or `rejected` |
| `evidence_needed` | Data, source, literature, or author input needed |
| `risk_if_wrong` | Why this decision matters |
| `author_decision_needed` | What the researcher must decide |
| `downstream_skill_route` | `research-data-builder`, `literature-matrix`, `research-analysis-runner`, `methods-reviewer`, `did-expert`, `ask_author`, or `none` |

## Rules

- `ready_for_handoff` requires a downstream skill other than `none`.
- `needs_author_decision` requires a concrete author decision.
- `needs_data_check` should route to `research-data-builder`.
- `needs_literature_check` should route to `literature-matrix`.
- Rejected choices must still record the reason in `risk_if_wrong`.
- Every decision must name the MIDA component it affects.
- Every decision row must preserve the matching `.aiss` `decision` id.
