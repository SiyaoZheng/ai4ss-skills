# Route Card Schema

Use `research_route_cards.csv` when comparing multiple ways to make a rough idea researchable. In the unified workflow this CSV is a human-readable mirror of `.aiss` `route` declarations, not a separate route language.

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
| `failure_signal` | What would show this route should pause, shrink, or stop |
| `feasibility_status` | `try_now`, `needs_material`, `needs_author_decision`, `needs_external_search`, `not_feasible`, or `handoff_ready` |
| `stop_reason` | Why the agent should stop before doing more |
| `researcher_decision_needed` | Decision that cannot be delegated to AI |
| `next_skill_route` | `research-data-builder`, `literature-matrix`, `methods-reviewer`, `academic-writing-scaffold`, `research-slides-builder`, `reviewer-response`, `did-expert`, `ask_author`, or `none` |

## Route Card Rules

- Open-ended tasks should have 2-4 route cards.
- At least one route should be small enough to attempt within a day.
- `first_action` must be an action on materials, sources, code skeletons, or decision scaffolds.
- `first_action` must not be final manuscript writing.
- `expected_first_output` must be inspectable: file, table shell, source list, data preview, figure shell, route memo, or prompt.
- `handoff_ready` requires a downstream `next_skill_route`, not `none`.
- `not_feasible` requires a concrete `failure_signal`.
- `model_scope`, `candidate_inquiry`, `possible_data_strategy`, and `possible_answer_strategy` are provisional. They exist to help `study-design-builder` select a `.aiss` route and declare MIDA, not to certify the design.
- When a durable `.aiss` artifact is produced, every non-rejected row should have a matching `route` declaration with `status: candidate` or `status: selected`.
