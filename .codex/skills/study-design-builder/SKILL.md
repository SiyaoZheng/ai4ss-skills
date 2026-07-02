---
name: study-design-builder
description: >
  Social-science study design builder for turning a selected research route, starter packet,
  literature clues, data affordances, or policy phenomenon into a design brief, estimand map,
  variable/source needs, analysis plan, and author decision register. Use after research-starter
  and before data construction, literature extraction, analysis execution, or methods audit when
  the user asks to make a research design concrete, define unit/outcome/treatment, compare design
  routes, build an analysis plan, or prepare a preregistration-style scaffold. Triggers: "study
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

When conceptual, construct, causal, or bridge structure matters, this skill also owns the `.aiss` research-model layer. The `.aiss` file is the computable representation of Model and parts of Inquiry/Diagnose; it does not replace the MIDA declaration.

## Hard Boundary

Do not write manuscript prose, final preregistration prose, final causal claims, or polished theory sections. Do not certify that an identification strategy is valid. Provide structured choices, evidence needs, risks, and author decision points.

## Workflow Contract

- Upstream inputs: `research_starter_packet.md`, `research_route_cards.csv`, seed literature notes, variable dictionaries, data previews, policy timelines, author notes, or an existing `research_model.aiss`.
- Produces: `docs/study_design_brief.md`, `docs/study_design_declaration.csv`, optionally `docs/design_decision_register.csv`, and when model structure matters `docs/research_model.aiss` plus `docs/ai4ss_check_report.txt`.
- Handoff fields: `route_id`, `model_scope`, `inquiry`, `study_type`, `unit_of_analysis`, `outcome`, `exposure_or_treatment`, `comparison`, `data_strategy`, `answer_strategy`, `diagnosands_or_gates`, `redesign_options`, `interpretation_boundary`, `author_decisions`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `commensurability_status`, `next_skill_route`.
- Downstream routes: `research-data-builder`, `literature-matrix`, `research-analysis-runner`, `methods-reviewer`, `did-expert`, or `ask_author`.

## Routing Boundaries

Use this skill after a route exists but before the project has a stable analysis plan. Hand data construction to `research-data-builder`, source discovery to `literature-matrix`, first analysis execution to `research-analysis-runner`, and identification audit to `methods-reviewer` or `$did-expert`.

## Workflow

```
Step -1: Orient to the selected route
-> Read starter packet, route cards, author notes, data previews, and seed sources.
-> Confirm route_id, study type, unit, material status, and hard boundaries.

Step 0: Declare MIDA
-> Build the design brief with explicit Model, Inquiry, Data Strategy, Answer Strategy, Diagnose, Redesign, and Report Boundary sections.
-> Mirror the declaration in `study_design_declaration.csv`.
-> Mark each element as author supplied, inferred from material or literature, agent proposed, or unresolved.

Step 0.5: Compile or update the AI4SS DSL model
-> When concepts, measurement bridges, causal implications, or theory-to-evidence links matter, create or update `research_model.aiss`.
-> Preserve stable `model_id`, `concept_id`, `causal_id`, and `bridge_id` values in the declaration sidecar.
-> Run `scripts/validate_ai4ss_model.py docs/research_model.aiss` when the toolchain is available, and save the output to `docs/ai4ss_check_report.txt`.
-> Treat checker errors as a design artifact failure, not as a cosmetic warning.

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
- `docs/research_model.aiss` and `docs/ai4ss_check_report.txt` when conceptual, causal, measurement, or bridge structure matters.
- Optional `docs/analysis_plan_scaffold.md` for the first analysis runner handoff.

## Script Utilities

- Run `scripts/validate_study_design_declaration.py <path>` to check the MIDA declaration sidecar.
- Run `scripts/validate_design_decisions.py <path>` to check the design decision register.
- Run `scripts/validate_ai4ss_model.py docs/research_model.aiss` to check the DSL model through the current `ai4ss-skills` parser/checker/bridge toolchain.

## Quality Bar

- Keep design choices traceable to route cards or supplied materials.
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
