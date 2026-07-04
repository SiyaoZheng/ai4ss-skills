---
name: study-design-builder
description: >
  Social-science study design builder for turning a selected research route, starter packet,
  literature clues, or data affordances into a design brief, estimand map, variable/source needs,
  analysis plan, and author decision register. Use after research-starter and before data
  construction, literature extraction, analysis execution, or methods audit when the user asks to
  make a selected research route concrete, define unit/outcome/treatment, compare design routes,
  build an analysis plan, or prepare a preregistration-style scaffold. Triggers: "study
  design", "research design brief", "estimand", "analysis plan", "turn route into design",
  "研究设计", "把选题落成设计", "变量和识别怎么定", "分析计划", "预分析计划".
---

# Study Design Builder

Turn a selected research route into a design object that data, literature, analysis, and audit skills can use.

## Scholar Workbench

This skill answers: "这个研究路线怎样落成可执行设计？" Its value is not auditing finished methods; it is making question, unit, measures, comparisons, evidence needs, and author decisions explicit before data or model work expands.

## Core Rule

Build a design brief, not a final identification judgment. The researcher owns novelty, theoretical contribution, causal credibility, and final claim strength.

## Methodology Foundation

This skill is the primary MIDA declaration layer. It turns a selected route into explicit `Model`, `Inquiry`, `Data strategy`, `Answer strategy`, and `Diagnose` fields before data construction or analysis expands.

`Estimand` belongs inside `Inquiry`, not in place of the whole design. For non-causal work, the same slot must name the target descriptive quantity, construct, classification target, process-tracing claim, or synthesis question.

This skill owns the `.aiss` workflow upgrade from provisional route to design. It marks one `.aiss` `route` as `selected`, writes seven `mida` declarations, records author-owned `decision` declarations, and then adds the model layer when conceptual, construct, causal, or bridge structure matters. When a theory workbench handoff exists, it may use validated `literature_theory_synthesis.csv`, `theory_rival_map.csv`, `theory_scope_map.csv`, and `theory_evidence.md` as evidence for existing `.aiss` `concept`, `claim`, `relation`, `causal`, `bridge`, or `model` declarations, while leaving novelty, rival choice, scope choice, and mechanism strength as author decisions.

## Hard Boundary

Do not write manuscript prose, final preregistration prose, final causal claims, or polished theory sections. Do not certify that an identification strategy is valid. Provide structured choices, evidence needs, risks, and author decision points.

## Workflow Contract

- Upstream inputs: `research_starter_packet.md`, `research_route_cards.csv`, route-only `research_model.aiss`, `literature_theory_synthesis.csv`, optional `theory_rival_map.csv`, optional `theory_scope_map.csv`, optional `theory_evidence.md`, seed literature notes, variable dictionaries, data previews, policy timelines, author notes, or an existing design-level `research_model.aiss`.
- Produces: `docs/study_design_brief.md`, `docs/study_design_declaration.csv`, optionally `docs/design_decision_register.csv`, `docs/research_model.aiss`, and `docs/ai4ss_check_report.txt`.
- Handoff fields: `route_id`, `route_decl_id`, `mida_id`, `decision_decl_id`, `model_scope`, `inquiry`, `study_type`, `unit_of_analysis`, `outcome`, `exposure_or_treatment`, `comparison`, `data_strategy`, `answer_strategy`, `diagnosands_or_gates`, `redesign_options`, `interpretation_boundary`, `author_decisions`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `commensurability_status`, `next_skill_route`.
- Downstream routes: `research-data-builder`, `literature-matrix`, `research-analysis-runner`, `methods-reviewer`, `did-expert`, or `ask_author`.

## Routing Boundaries

Use this skill after a route exists but before the project has a stable analysis plan. Hand data construction to `research-data-builder`, source discovery to `literature-matrix`, first analysis execution to `research-analysis-runner`, and identification audit to `methods-reviewer` or `$did-expert`.

If the user only has a vague topic or policy phenomenon and no selected route,
stop and route to `research-starter` or `ask_author`; do not synthesize a full
MIDA declaration from a blank slate.

## Workflow

```
Step -1: Orient to the selected route
-> Read starter packet, route cards, author notes, data previews, and seed sources.
-> Confirm route_id, study type, unit, material status, and hard boundaries.
-> If no route_id or provisional `.aiss` `route` exists, stop with a handoff to `research-starter` or `ask_author`.

Step 0: Declare MIDA
-> Build the design brief with explicit Model, Inquiry, Data Strategy, Answer Strategy, Diagnose, Redesign, and Report Boundary sections.
-> Update `research_model.aiss`: mark the selected `.aiss` `route` as `selected` and add exactly seven `mida` declarations for Model, Inquiry, Data Strategy, Answer Strategy, Diagnose, Redesign, and Report Boundary.
-> Mirror the `.aiss` declaration in `study_design_declaration.csv`.
-> Mark each element as author supplied, inferred from material or literature, agent proposed, or unresolved.

Step 0.5: Compile or update the `.aiss` model layer
-> When concepts, measurement bridges, causal implications, or theory-to-evidence links matter, add or update `concept`, `claim`, `attribute`, `causal`, `bridge`, and `model` declarations in the same `research_model.aiss`.
-> If `literature_theory_synthesis.csv` is present, use its `proposed_aiss_object`, `source_paper_ids`, `rival_or_boundary`, `observable_implication`, `evidence_strength`, and `author_decision_needed` fields to decide which model-layer objects are proposed, diagnosed, blocked, or left for the author.
-> If the full theory workbench is present, run or require `scripts/validate_theory_workbench.py <workbench-dir>` before using it.
-> Only workbench objects that pass validation and are marked `ready_for_aiss` may be compiled into or used to update `.aiss` model-layer declarations.
-> Route rival explanations, scope drift, unresolved theoretical contribution, and mechanism-strength choices into `design_decision_register.csv` and `.aiss` `decision` declarations instead of model facts.
-> In `study_design_declaration.csv`, cite `literature_theory_synthesis.csv` in `evidence_source` for affected MIDA rows; do not add new columns.
-> Preserve stable `route_decl_id`, `mida_id`, `decision_decl_id`, `model_id`, `concept_id`, `causal_id`, and `bridge_id` values in the declaration sidecars.
-> Run `scripts/validate_ai4ss_model.py docs/research_model.aiss` when the toolchain is available, and save the output to `docs/ai4ss_check_report.txt`.
-> Treat `aiss.py lint` errors as a design artifact failure, not as a cosmetic warning.

Step 1: Map design choices
-> List candidate descriptive, causal, text, qualitative, or mixed-method designs that fit the route.
-> For each choice, name data needs, literature needs, risks, and what would make the choice infeasible.

Step 2: Create analysis plan scaffold
-> Define the first table/figure/model/coding output that would test feasibility.
-> Specify required inputs and validation checks.
-> Do not run analysis unless the user explicitly asks and inputs are ready; hand execution to `research-analysis-runner`.

Step 3: Register decisions
-> Produce a design decision register with status, evidence needed, author decision, and downstream route.
-> Stop when novelty, theory, causal credibility, or public claim strength requires author judgment.
```

## Default Outputs

- `docs/study_design_brief.md`.
- `docs/study_design_declaration.csv`.
- `docs/design_decision_register.csv` when multiple design choices or unresolved decisions exist.
- `docs/research_model.aiss` with selected `route`, seven `mida` declarations, `decision` declarations, and model-layer declarations when conceptual, causal, measurement, or bridge structure matters.
- `docs/ai4ss_check_report.txt`.
- Optional `docs/analysis_plan_scaffold.md` for the first analysis runner handoff.

## Script Utilities

- Run `scripts/validate_study_design_declaration.py <path>` to check the MIDA declaration sidecar.
- Run `scripts/validate_design_decisions.py <path>` to check the design decision register.
- Run `scripts/validate_theory_workbench.py <workbench-dir>` before consuming full theory workbench sidecars.
- Run `scripts/validate_ai4ss_model.py docs/research_model.aiss` to check the DSL model through `aiss.py compile`, `aiss.py lint`, and `aiss.py run`.

## Quality Bar

- Keep design choices traceable to route cards or supplied materials.
- Keep theory-mapping choices traceable to verified literature synthesis sidecars when they come from literature.
- Consume only validated `ready_for_aiss` theory workbench objects as `.aiss` model-layer input.
- Separate feasible first analysis from full-paper ambition.
- Do not default every project to causal panel regression.
- Record unresolved author decisions instead of smoothing them into a fake design.
- Make downstream handoff explicit.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [design-workflow.md](references/design-workflow.md) | Design brief shape, design components, and stop rules | Building a study design brief |
| [declaration-schema.md](references/declaration-schema.md) | MIDA declaration CSV schema and validator rules | Creating or validating `study_design_declaration.csv` |
| [decision-register-schema.md](references/decision-register-schema.md) | CSV schema and allowed design statuses/routes | Creating or validating decision registers |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for design intake, route comparison, analysis plan scaffolds, and handoff | Turning a selected route into a design task |
| [worked-example.md](references/worked-example.md) | Digital-government route to design brief example | Teaching or demonstrating the skill |
