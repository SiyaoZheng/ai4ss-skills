---
name: research-starter
description: >
  First-loop social-science research starter for turning a vague topic, rough question,
  source pile, dataset folder, or policy phenomenon into `.aiss` route declarations, a minimum viable
  study, and the next executable research action. Use before provenance, robustness,
  literature-matrix, data-pipeline, or writing-scaffold work when the user asks how to
  start a study, make a research idea concrete, choose among feasible research routes,
  or use AI to move from zero to one. Triggers: "start a research project", "research
  idea", "from zero to one", "minimum viable study", "route declaration", "what can I do next",
  "我想做一个研究", "从无到有", "选题怎么落地", "先把研究做出来", "下一步怎么推进".
---

# Research Starter

Start the first research loop. This skill turns a loose topic plus available materials into a concrete research object that later skills can inspect.

## Scholar Workbench

This skill answers: "这个研究怎么先动起来？" Its value is not robustness or provenance; it is making a topic, material pile, or intuition become `.aiss` route declarations, a minimum viable study, and one next executable action.

## Methodology Foundation

This skill is the pre-declaration layer of the MIDA spine: it sketches possible `Model`, `Inquiry`, `Data strategy`, and `Answer strategy` routes before the researcher commits to a design.

Each route declaration must preserve a rough inquiry or target quantity, available evidence, possible first answer strategy, diagnosability, failure signal, and author decision point. These sketches are not valid designs until `study-design-builder` selects one route and declares the full MIDA object.

Starter output may name candidate concepts, causal links, or empirical bridges, but it must not create a final model layer. When the work needs a durable research object, create or update `research_model.aiss` with provisional `.aiss` `route` declarations only; `study-design-builder` later marks one route `selected`, adds seven `mida` declarations, and only then adds stable model/bridge objects when warranted.

## Core Rule

Produce `.aiss` research objects first. The default workflow output is
`research_model.aiss` with candidate `route` declarations, stop reasons, and
researcher decision points. Chat summaries and any AI-assisted working prose are
display only, not workflow state.

## AI4SS Runtime Gate

This is the only research-factory skill allowed to start from a rough topic
without an existing AI4SS object. It must not leave the workflow as prose-only:
when the work will continue beyond intake, create or update `research_model.aiss`
with provisional `.aiss` `route` declarations. If a durable `.aiss` route cannot
be created, stop with a blocked handoff and a concrete reason; do not route
downstream as if AI4SS had been declared.

## Workflow Contract

- Upstream inputs: rough topic, source pile, dataset folder, policy phenomenon, author notes, or a request for "what can I do next?"
- Produces: route-only `docs/research_model.aiss` with candidate `.aiss` `route` declarations, human-accountable `decision` declarations, and a first-pass transparency target; optional chat-facing notes may be displayed from it.
- Handoff fields: `route_id`, `route_decl_id`, `ai4ss_model_path`, `research_question`, `model_scope`, `candidate_inquiry`, `candidate_concepts`, `candidate_causal_links`, `candidate_empirical_bridges`, `possible_data_strategy`, `possible_answer_strategy`, `study_type`, `unit_of_analysis`, `materials_available`, `materials_gap`, `registration_relevance`, `transparency_level_target`, `first_action`, `failure_signal`, `stop_reason`, `researcher_decision_needed`, `aiss_check_status`, `next_skill_route`.
- Downstream routes: `study-design-builder`, `research-data-builder`, `literature-matrix`, `methods-reviewer`, `academic-writing-scaffold`, `research-slides-builder`, `did-expert`, or `ask_author`.

## Single Manuscript-Facing Boundary

AI may draft, revise, or sketch working text only when it is clearly marked as
AI-assisted and not direct-submission ready. The only disallowed
manuscript-facing output is hidden-AI or submission-ready presentation without
AI contribution disclosure, human accountability, outlet-policy status, and
direct-submission status.

## Routing Boundaries

Use this skill before the project has a chosen route, dataset pipeline, verified literature base, model table, or writing scaffold. After a route is selected, hand off:

- Data construction or extraction to `research-data-builder`.
- Literature search, screening, or extraction to `literature-matrix`.
- Study design concretization to `study-design-builder`.
- First-pass analysis execution to `research-analysis-runner` only after a design source and analysis-ready data exist.
- Identification and result-claim validity to `methods-reviewer`, or `$did-expert` when DID/event-study is central.
- Section planning and claim slots to `academic-writing-scaffold`.
- Research decks to `research-slides-builder`.

Do not duplicate downstream validators. This skill makes the first object exist; downstream skills audit and deepen it.

## Workflow

```
Step -1: Intake only what is needed
-> Capture four fields: one-sentence question or phenomenon, available materials, hard boundaries, and the one action the researcher hopes AI can do next.
-> If information is missing, state what can be done now and what must be asked from the researcher.

Step 0: Inventory materials
-> Inspect the file tree, notes, variable dictionaries, seed papers, data previews, or source links provided.
-> Separate usable materials, uncertain materials, unavailable materials, and confidential or off-limits materials.

Step 1: Build candidate route declarations
-> For open-ended topics, produce 2-4 `.aiss` `route` declarations before choosing.
-> Each route declaration must name the question, phenomenon, unit, material path, first action, expected first output, feasibility status, stop reason, researcher decision, and next skill route.
-> Mark whether the route is registration-relevant and what transparency target it implies for materials, data, code, and reporting.
-> When the work will continue in the research-factory workflow, write each candidate directly as a `.aiss` `route` declaration with `status: candidate`, not as a final model.
-> Do not send data, literature, analysis, review, writing, slide, or revision work downstream unless `route_decl_id` and `ai4ss_model_path` are present in `.aiss` or the handoff is explicitly blocked.
-> If the user already picked one route, still record rejected alternatives briefly.

Step 2: Define a minimum viable study
-> Choose the smallest study that can produce one checkable observation, table shell, figure shell, source matrix seed, or data feasibility result.
-> Do not jump to a full model battery, systematic review, or polished argument.

Step 3: Run or specify one next action
-> Execute the next action only when inputs are present and the action is safe.
-> Otherwise write the exact handoff prompt the researcher can use next.
-> Keep the action material-to-action: inspect, sample, retrieve, sketch, scaffold, or draft AI-disclosed working text through the proper downstream skill.

Step 4: Stop deliberately
-> End with `stop_reason`, `researcher_decision_needed`, `handoff_prompt`, and `next_skill_route`.
-> If the route is not feasible, say so and propose a smaller route or abandon path.
```

## Default Outputs

- `docs/research_model.aiss` with candidate `route` declarations and author `decision` declarations.
- Optional author-facing chat note generated from `.aiss`, clearly marked as non-canonical.
- Runtime logs only when referenced as `.aiss` evidence artifacts.

## Script Utilities

- Run `python3 dsl/scripts/aiss.py compile <path-to-research_model.aiss>` and `python3 dsl/scripts/aiss.py lint <path-to-research_model.aiss>` when a route-only `.aiss` artifact is produced.
- Treat validator failures as starter artifacts, not terminal noise: record the failed command, the exact schema or import error, the fix, and the rerun result before handing off.
- If an installed validator cannot import `ai4ss_factory_contracts`, set `AI4SS_SKILLS_ROOT` to the `ai4ss-skills` source checkout and rerun; do not ignore the validation gate.

## Quality Bar

- Start from feasibility, not compliance.
- Prefer concrete `.aiss` route declarations over general advice.
- Keep at least one route small enough to attempt within a day.
- Treat data availability, source access, and variable existence as first-class findings.
- Include a failure signal for every next action.
- Preserve academic authorship boundaries and AI-use disclosure needs.
- Use downstream skills only after a research object exists.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [starter-workflow.md](references/starter-workflow.md) | First-loop workflow, route-declaration shape, and stop rules | Starting any zero-to-one research task |
| [minimum-viable-study.md](references/minimum-viable-study.md) | Minimum viable study patterns across descriptive, causal, text, qualitative, and mixed-method projects | Choosing the smallest credible first study |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for intake, route declarations, MVS selection, first action, and handoff | Turning a loose request into an agent task |
| [worked-example.md](references/worked-example.md) | Digital-government and firm-innovation route-declaration example | Teaching or demonstrating the skill |
