---
name: study-design-builder
description: >
  Social-science study design builder for turning a selected research route, route declarations,
  literature clues, or data affordances into `.aiss` MIDA declarations, estimand map,
  variable/source needs, analysis plan, and automatic design-choice declarations. Use after research-starter and before source
  acquisition, data construction, literature extraction, analysis execution, or methods audit when the user asks to
  make a selected research route concrete, define unit/outcome/treatment, compare design routes,
  build an analysis plan, or prepare a preregistration-style scaffold. Triggers: "study
  design", "research design brief", "estimand", "analysis plan", "turn route into design",
  "研究设计", "把选题落成设计", "变量和识别怎么定", "分析计划", "预分析计划".
---

# Study Design Builder

Turn a selected research route into a design object that data, literature, analysis, and audit skills can use.

## Scholar Workbench

This skill answers: "这个研究路线怎样落成可执行设计？" Its value is not auditing finished methods; it is making question, unit, measures, comparisons, evidence needs, and automatic design choices explicit before data or model work expands.

## Core Rule

Build an executable design brief that can carry a publication-level draft PDF. When several designs are possible, automatically choose the strongest defensible one and record why.

## Full-Auto Harness Contract

When invoked by an automatic research harness, this skill must not pause for
human choice or return any terminal no-progress state. If no selected route exists, select the strongest candidate route in
`.aiss`; if no route exists, create a route using `research-starter` logic and
continue. If a MIDA field is uncertain, infer the best defensible value from the
route, data affordances, literature, and source files, record the assumption,
and continue. The target artifact is a publication-level `paper/full_draft.pdf`.

## AI4SS Runtime Gate

This skill owns the upgrade from route to executable AI4SS design. It must not
produce a design outside `.aiss`. A valid handoff requires `.ai4ss/research_model.aiss`
with one selected `.aiss` `route`, exactly seven `mida` declarations, stable
`route_decl_id` / `mida_id` values where applicable, and a recorded
`ai4ss_check_status`. If no route exists, create or select one automatically.
If MIDA cannot be validated on the first pass, repair the declarations, record
the failed command and fix, rerun validation, and continue.

## Methodology Foundation

This skill is the primary MIDA declaration layer. It turns a selected route into explicit `Model`, `Inquiry`, `Data strategy`, `Answer strategy`, and `Diagnose` fields before data construction or analysis expands.

`Estimand` belongs inside `Inquiry`, not in place of the whole design. For non-causal work, the same slot must name the target descriptive quantity, construct, classification target, process-tracing claim, or synthesis question.

This skill owns the `.aiss` workflow upgrade from provisional route to design. It marks one `.aiss` `route` as `selected`, writes seven `mida` declarations, records inferred assumptions and design-choice declarations, and then adds the model layer when conceptual, construct, causal, or bridge structure matters. When literature or theory evidence exists, it must be represented as `.aiss` `paper`, `source`, `span`, `claim`, `relation`, `check`, or `decision` declarations before it updates `.aiss` `concept`, `causal`, `bridge`, or `model` declarations.

## Workspace Contract

Follow `docs/research_workspace_contract.md`. Durable workflow state belongs in
`.ai4ss/research_model.aiss`; generated data, output, logs, and PDFs must be
produced through `make` targets, with `make all` as the final orchestration path.

## .aiss State Machine

When `.ai4ss/research_model.aiss` exists, run
`python3 dsl/scripts/aiss.py state .ai4ss/research_model.aiss` before deciding
the next route. When this skill starts, completes, fails, or observes a
watchdog heartbeat in an automatic harness, record that runtime fact as an
`.aiss` `event` declaration or return a deterministic
`aiss.py transition --event ...` fragment for merge. Events do not replace
semantic updates: if the skill resolves a repair/check status, update the
relevant `route`, `mida`, `decision`, `check`, `artifact`, or claim-support
declaration too.

## Single Manuscript-Facing Boundary

AI may draft working protocol, preregistration, theory, or manuscript text when
AI contribution disclosure, accountability language, outlet-policy status, and
direct-submission status are explicit in the artifact. This skill does not hide
identification risk; it records design choices, evidence needs, risks,
assumptions, and claim boundaries so the draft PDF can state them.

## Workflow Contract

- Upstream inputs: route-only `.ai4ss/research_model.aiss`, seed literature notes, variable dictionaries, data previews, policy timelines, author notes, or an existing design-level `.ai4ss/research_model.aiss`.
- Produces: `.ai4ss/research_model.aiss` with selected `route`, seven `mida` declarations, automatic design-choice declarations, registration/protocol/analysis-plan status, model declarations, and check declarations; optional chat-facing notes may be displayed from `.aiss`.
- Handoff fields: `route_id`, `route_decl_id`, `mida_id`, `model_scope`, `inquiry`, `study_type`, `unit_of_analysis`, `outcome`, `exposure_or_treatment`, `comparison`, `data_strategy`, `answer_strategy`, `diagnosands_or_gates`, `registration_status`, `protocol_path`, `analysis_plan_path`, `deviation_log_status`, `redesign_options`, `interpretation_boundary`, `assumptions_to_disclose`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `commensurability_status`, `next_skill_route`.
- Downstream routes: `public-data-sources`, `research-data-builder`, `literature-matrix`, `research-analysis-runner`, `methods-reviewer`, or `did-expert`.

## Routing Boundaries

Use this skill after a route exists but before the project has a stable analysis plan. Hand real observed source acquisition to `public-data-sources`, analysis-sample construction from acquired sources to `research-data-builder`, source-backed theory discovery to `literature-matrix`, first analysis execution to `research-analysis-runner`, and identification audit to `methods-reviewer` or `$did-expert`.

If the user only has a vague topic or policy phenomenon and no selected route,
create candidate routes, select the best one automatically, and then declare
MIDA for that route rather than returning a blank handoff.

## Workflow

```
Step -1: Orient to the selected route
-> Read `.ai4ss/research_model.aiss`, author notes, data previews, and seed sources.
-> Confirm route_id, study type, unit, material status, and hard boundaries.
-> If no route_id or provisional `.aiss` `route` exists, create candidate routes and select the strongest one.
-> Do not create data, literature, analysis, review, writing, slide, or revision outputs until `.ai4ss/research_model.aiss` contains the selected route and MIDA declarations.

Step 0: Declare MIDA
-> Build the design brief with explicit Model, Inquiry, Data Strategy, Answer Strategy, Diagnose, Redesign, and Report Boundary sections.
-> Update `.ai4ss/research_model.aiss`: mark the selected `.aiss` `route` as `selected` and add exactly seven `mida` declarations for Model, Inquiry, Data Strategy, Answer Strategy, Diagnose, Redesign, and Report Boundary.
-> Record each element as supplied, inferred from material or literature, agent selected, or uncertainty-to-disclose inside the `.aiss` declaration metadata or linked `decision` declarations.

Step 0.5: Compile or update the `.aiss` model layer
-> When concepts, measurement bridges, causal implications, or theory-to-evidence links matter, add or update `concept`, `claim`, `attribute`, `causal`, `bridge`, and `model` declarations in the same `.ai4ss/research_model.aiss`.
-> If literature or theory evidence is present, first encode it as `.aiss` source/span/claim/check/decision declarations, then use those declarations to decide which model-layer objects are proposed, diagnosed, revised, or carried as explicit assumptions.
-> Route rival explanations, scope drift, unresolved theoretical contribution, and mechanism-strength choices into `.aiss` `decision` declarations instead of model facts.
-> Preserve stable `route_decl_id`, `mida_id`, `decision_decl_id`, `model_id`, `concept_id`, `causal_id`, and `bridge_id` values in `.aiss`.
-> Run `scripts/validate_ai4ss_model.py .ai4ss/research_model.aiss` when the toolchain is available, and save the output to `.ai4ss/checks/ai4ss_check_report.txt`.
-> Treat `aiss.py lint` errors as repair work: record the error, fix the declaration, and rerun.

Step 1: Map design choices
-> List candidate descriptive, causal, text, qualitative, or mixed-method designs that fit the route.
-> For each choice, name real observed source needs, literature needs, risks, and what would make the choice infeasible.
-> Reject designs whose empirical answer requires synthetic, simulated,
   hypothetical, illustrative, generated, DGP-created, random-draw,
   benchmark-calibrated, or literature-parameter-imputed data. Automatically
   choose the strongest redesign with an observed-data route.

Step 2: Create registration, protocol, and analysis-plan scaffold
-> Define the first table/figure/model/coding output that would test feasibility.
-> Specify required inputs and validation checks.
-> Record `registration_status`, `protocol_path`, `analysis_plan_path`, and `deviation_log_status` so later skills can distinguish preregistered plans, declared deviations, and post-hoc exploratory additions.
-> Do not run analysis inside this skill unless it is a small design-feasibility check; otherwise create the exact analysis-plan file and hand execution to `research-analysis-runner`.

Step 3: Register decisions
-> Record `.aiss` `decision` declarations with status, evidence needed, automatic design choice, assumption to disclose, and downstream route.
-> When novelty, theory, causal credibility, or public claim strength is uncertain, choose the strongest defensible claim boundary and require later evidence expansion, not a human stop.
```

## Default Outputs

- `.ai4ss/research_model.aiss` with selected `route`, seven `mida` declarations, automatic design-choice declarations, registration/protocol/analysis-plan status, and model-layer declarations when conceptual, causal, measurement, or bridge structure matters.
- `.ai4ss/checks/ai4ss_check_report.txt`.
- Author-facing design summary or analysis-plan scaffold in the chat response, generated from `.aiss` and clearly marked as non-canonical.

## Script Utilities

- Run `scripts/validate_ai4ss_model.py .ai4ss/research_model.aiss` to check the DSL model through `aiss.py compile`, `aiss.py lint`, and `aiss.py run`.

## Quality Bar

- Keep design choices traceable to `.aiss` route declarations or supplied materials.
- Keep theory-mapping choices traceable to verified `.aiss` literature/source declarations when they come from literature.
- Consume only validated `.aiss` evidence declarations as model-layer input.
- Make the first feasible analysis serve the publication-level draft PDF.
- Make source acquisition an explicit design dependency; do not route empirical
  work directly to sample construction unless a verified real observed source
  artifact already exists.
- Do not default every project to causal panel regression.
- Record assumptions and claim boundaries instead of smoothing uncertainty into a fake design.
- Make downstream handoff explicit.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [design-workflow.md](references/design-workflow.md) | Design brief shape, design components, and stop rules | Building a study design brief |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for design intake, route comparison, analysis plan scaffolds, and handoff | Turning a selected route into a design task |
| [worked-example.md](references/worked-example.md) | Digital-government route to design brief example | Teaching or demonstrating the skill |
