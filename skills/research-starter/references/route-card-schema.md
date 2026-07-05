# Route Card Schema

Use `.aiss route declarations` when comparing multiple ways to make a rough idea researchable. In the unified workflow this CSV is a human-readable mirror of `.aiss` `route` declarations, not a separate route language.

## Required Columns

| column | meaning |
|---|---|
| `route_id` | Stable id such as `R1` |
| `route_decl_id` | Stable `.aiss` route id such as `project.route_r1`, or `not_created:<reason>` |
| `working_title` | Short provisional title |
| `research_question` | One-sentence question, not a finished contribution claim |
| `phenomenon` | Empirical or theoretical phenomenon being studied |
| `model_scope` | Provisional unit, population, setting, mechanism, and scope conditions |
| `candidate_inquiry` | Provisional estimand, descriptive quantity, measurement target, classification target, process-tracing claim, or synthesis question |
| `possible_data_strategy` | Candidate source, sample, measurement, extraction, linkage, or missingness plan |
| `possible_answer_strategy` | Candidate estimator, coding rule, synthesis rule, diagnostic comparison, table/figure shell, or qualitative inference procedure |
| `study_type` | `descriptive`, `causal`, `prediction`, `text_analysis`, `case_comparison`, `qualitative`, `mixed_methods`, or `theory_mapping` |
| `unit_of_analysis` | Person, firm, city-year, policy document, interview, article, case, or other unit |
| `materials_available` | Existing files, source links, notes, data previews, or seed papers |
| `materials_gap` | Missing source, variable, permission, sample boundary, or theory input |
| `first_action` | One safe action the agent can do next |
| `expected_first_output` | The concrete output of that one action |
| `failure_signal` | What would show this route should be repaired, narrowed, or replaced by the next-ranked route |
| `feasibility_status` | `try_now`, `needs_material_search`, `needs_external_search`, `needs_design_repair`, `not_feasible_after_search`, or `handoff_ready` |
| `selection_rationale` | Why this route was selected or ranked below the selected route |
| `assumptions_to_disclose` | Assumptions the draft PDF must state if the route proceeds |
| `next_skill_route` | `study-design-builder`, `public-data-sources`, `research-data-builder`, `literature-matrix`, `methods-reviewer`, `academic-writing-scaffold`, `research-slides-builder`, `reviewer-response`, `did-expert`, `research-analysis-runner`, or `none` |

## Route Card Rules

- Open-ended tasks should have 2-4 route cards.
- At least one route should be small enough to attempt within a day.
- `first_action` must be an action on materials, sources, code skeletons, or decision scaffolds.
- `first_action` must not present AI-assisted manuscript writing as no-AI or
  direct-submission ready.
- `expected_first_output` must be inspectable: file, table shell, source list, data preview, figure shell, route memo, or prompt.
- `handoff_ready` requires a downstream `next_skill_route`, not `none`.
- `not_feasible_after_search` requires a concrete `failure_signal` and the next-ranked route to try.
- `model_scope`, `candidate_inquiry`, `possible_data_strategy`, and `possible_answer_strategy` are provisional. They exist to help `study-design-builder` select a `.aiss` route and declare MIDA, not to certify the design.
- When a durable `.aiss` artifact is produced, every retained row should have a matching `route` declaration and exactly one route should be selected for the next skill.
