---
name: study-design-builder
description: >
  Social-science study design builder for turning a selected research route, route declarations,
  literature clues, or data affordances into `.aiss` MIDA declarations, estimand map,
  variable/source needs, analysis plan, and author decision declarations. Use after research-starter and before data
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

## AI4SS Runtime Gate

This skill owns the upgrade from route to executable AI4SS design. It must not
produce a design outside `.aiss`. A valid handoff requires `research_model.aiss`
with one selected `.aiss` `route`, exactly seven `mida` declarations, stable
`route_decl_id` / `mida_id` / `decision_decl_id` values where applicable, and a
recorded `ai4ss_check_status`. If no route exists, stop and route to
`research-starter` or `ask_author`; if MIDA cannot be declared, stop with a
blocked design artifact instead of letting downstream skills proceed.

## Methodology Foundation

This skill is the primary MIDA declaration layer. It turns a selected route into explicit `Model`, `Inquiry`, `Data strategy`, `Answer strategy`, and `Diagnose` fields before data construction or analysis expands.

`Estimand` belongs inside `Inquiry`, not in place of the whole design. For non-causal work, the same slot must name the target descriptive quantity, construct, classification target, process-tracing claim, or synthesis question.

This skill owns the `.aiss` workflow upgrade from provisional route to design. It marks one `.aiss` `route` as `selected`, writes seven `mida` declarations, records human-accountable `decision` declarations, and then adds the model layer when conceptual, construct, causal, or bridge structure matters. When literature or theory evidence exists, it must be represented as `.aiss` `paper`, `source`, `span`, `claim`, `relation`, `check`, or `decision` declarations before it updates `.aiss` `concept`, `causal`, `bridge`, or `model` declarations.

## Single Manuscript-Facing Boundary

AI may draft working protocol, preregistration, theory, or manuscript text only
when it is marked as AI-assisted and not direct-submission ready. The only
disallowed manuscript-facing output is hidden-AI or submission-ready
presentation without AI contribution disclosure, human accountability,
outlet-policy status, and direct-submission status. This skill still does not
certify that an
identification strategy is valid; it records design choices, evidence needs,
risks, and author decision points.

## Workflow Contract

- Upstream inputs: route-only `research_model.aiss`, seed literature notes, variable dictionaries, data previews, policy timelines, author notes, or an existing design-level `research_model.aiss`.
- Produces: `docs/research_model.aiss` with selected `route`, seven `mida` declarations, author `decision` declarations, registration/protocol/analysis-plan status, model declarations, and check declarations; optional chat-facing notes may be displayed from `.aiss`.
- Handoff fields: `route_id`, `route_decl_id`, `mida_id`, `decision_decl_id`, `model_scope`, `inquiry`, `study_type`, `unit_of_analysis`, `outcome`, `exposure_or_treatment`, `comparison`, `data_strategy`, `answer_strategy`, `diagnosands_or_gates`, `registration_status`, `protocol_path`, `analysis_plan_path`, `deviation_log_status`, `redesign_options`, `interpretation_boundary`, `author_decisions`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `commensurability_status`, `next_skill_route`.
- Downstream routes: `research-data-builder`, `literature-matrix`, `research-analysis-runner`, `methods-reviewer`, `did-expert`, or `ask_author`.

## Routing Boundaries

Use this skill after a route exists but before the project has a stable analysis plan. Hand data construction to `research-data-builder`, source discovery to `literature-matrix`, first analysis execution to `research-analysis-runner`, and identification audit to `methods-reviewer` or `$did-expert`.

If the user only has a vague topic or policy phenomenon and no selected route,
stop and route to `research-starter` or `ask_author`; do not synthesize a full
MIDA declaration from a blank slate.

## Workflow

```
Step -1: Orient to the selected route
-> Read `research_model.aiss`, author notes, data previews, and seed sources.
-> Confirm route_id, study type, unit, material status, and hard boundaries.
-> If no route_id or provisional `.aiss` `route` exists, stop with a handoff to `research-starter` or `ask_author`.
-> Do not create data, literature, analysis, review, writing, slide, or revision outputs until `research_model.aiss` contains the selected route and MIDA declarations.

Step 0: Declare MIDA
-> Build the design brief with explicit Model, Inquiry, Data Strategy, Answer Strategy, Diagnose, Redesign, and Report Boundary sections.
-> Update `research_model.aiss`: mark the selected `.aiss` `route` as `selected` and add exactly seven `mida` declarations for Model, Inquiry, Data Strategy, Answer Strategy, Diagnose, Redesign, and Report Boundary.
-> Record each element as author supplied, inferred from material or literature, agent proposed, or unresolved inside the `.aiss` declaration metadata or linked `decision` declarations.

Step 0.5: Compile or update the `.aiss` model layer
-> When concepts, measurement bridges, causal implications, or theory-to-evidence links matter, add or update `concept`, `claim`, `attribute`, `causal`, `bridge`, and `model` declarations in the same `research_model.aiss`.
-> If literature or theory evidence is present, first encode it as `.aiss` source/span/claim/check/decision declarations, then use those declarations to decide which model-layer objects are proposed, diagnosed, blocked, or left for the author.
-> Route rival explanations, scope drift, unresolved theoretical contribution, and mechanism-strength choices into `.aiss` `decision` declarations instead of model facts.
-> Preserve stable `route_decl_id`, `mida_id`, `decision_decl_id`, `model_id`, `concept_id`, `causal_id`, and `bridge_id` values in `.aiss`.
-> Run `scripts/validate_ai4ss_model.py docs/research_model.aiss` when the toolchain is available, and save the output to `docs/ai4ss_check_report.txt`.
-> Treat `aiss.py lint` errors as a design artifact failure, not as a cosmetic warning.

Step 1: Map design choices
-> List candidate descriptive, causal, text, qualitative, or mixed-method designs that fit the route.
-> For each choice, name data needs, literature needs, risks, and what would make the choice infeasible.

Step 2: Create registration, protocol, and analysis-plan scaffold
-> Define the first table/figure/model/coding output that would test feasibility.
-> Specify required inputs and validation checks.
-> Record `registration_status`, `protocol_path`, `analysis_plan_path`, and `deviation_log_status` so later skills can distinguish preregistered plans, author-approved deviations, and post-hoc exploratory additions.
-> Do not run analysis unless the user explicitly asks and inputs are ready; hand execution to `research-analysis-runner`.

Step 3: Register decisions
-> Record `.aiss` `decision` declarations with status, evidence needed, author decision, and downstream route.
-> Stop when novelty, theory, causal credibility, or public claim strength requires author judgment.
```

## Default Outputs

- `docs/research_model.aiss` with selected `route`, seven `mida` declarations, `decision` declarations, registration/protocol/analysis-plan status, and model-layer declarations when conceptual, causal, measurement, or bridge structure matters.
- `docs/ai4ss_check_report.txt`.
- Author-facing design summary or analysis-plan scaffold in the chat response, generated from `.aiss` and clearly marked as non-canonical.

## Script Utilities

- Run `scripts/validate_ai4ss_model.py docs/research_model.aiss` to check the DSL model through `aiss.py compile`, `aiss.py lint`, and `aiss.py run`.

## Quality Bar

- Keep design choices traceable to `.aiss` route declarations or supplied materials.
- Keep theory-mapping choices traceable to verified `.aiss` literature/source declarations when they come from literature.
- Consume only validated `.aiss` evidence declarations as model-layer input.
- Separate feasible first analysis from full-paper ambition.
- Do not default every project to causal panel regression.
- Record unresolved author decisions instead of smoothing them into a fake design.
- Make downstream handoff explicit.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [design-workflow.md](references/design-workflow.md) | Design brief shape, design components, and stop rules | Building a study design brief |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for design intake, route comparison, analysis plan scaffolds, and handoff | Turning a selected route into a design task |
| [worked-example.md](references/worked-example.md) | Digital-government route to design brief example | Teaching or demonstrating the skill |
