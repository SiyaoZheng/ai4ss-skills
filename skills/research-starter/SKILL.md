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

This skill is the pre-declaration layer of the MIDA spine: it sketches possible `Model`, `Inquiry`, `Data strategy`, and `Answer strategy` routes, scores them, and automatically selects the strongest feasible route for the next skill.

Each route declaration must preserve a rough inquiry or target quantity, available evidence, possible first answer strategy, diagnosability, failure signal, and selection rationale. These sketches are not valid designs until `study-design-builder` declares the full MIDA object.

Starter output may name candidate concepts, causal links, or empirical bridges, but it must not create a final model layer. When the work needs a durable research object, create or update `.ai4ss/research_model.aiss` with provisional `.aiss` `route` declarations and one selected best route; `study-design-builder` adds seven `mida` declarations and stable model/bridge objects when warranted.

## Core Rule

Produce `.aiss` research objects first. The default workflow output is
`.ai4ss/research_model.aiss` with candidate `route` declarations, one
automatically selected best route, selection rationale, and the next executable
research action. Chat summaries and any AI-assisted working prose are display
only, not workflow state.

## Full-Auto Harness Contract

When invoked by an automatic research harness, this skill must not pause for
human choice or return any terminal no-progress state. Missing information becomes an explicit assumption, source-search task,
data-inspection task, or downstream skill handoff. The skill must choose the
best route itself using publication-level draft potential, source/data
availability from real observed public or authorized sources, credible answer
strategy, diagnosability, and time-to-first analysis as ranking criteria. The
target artifact is a publication-level
`paper/full_draft.pdf`; route selection must optimize for getting that PDF to a
defensible scholarly draft, not for producing a non-draft placeholder.

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

## AI4SS Runtime Gate

This is the only research-factory skill allowed to start from a rough topic
without an existing AI4SS object. It must not leave the workflow as prose-only:
when the work will continue beyond intake, create or update
`.ai4ss/research_model.aiss` with provisional `.aiss` `route` declarations and
one selected route. If an `.aiss` file is absent, create the smallest valid
route-only file, run validation, repair schema issues, and continue with the
selected route.

## Workflow Contract

- Upstream inputs: rough topic, source pile, dataset folder, policy phenomenon, author notes, or a request for "what can I do next?"
- Produces: route-only `.ai4ss/research_model.aiss` with candidate `.aiss` `route` declarations, one selected best route, route-ranking rationale, inferred assumptions, and a first-pass transparency target; optional chat-facing notes may be displayed from it.
- Handoff fields: `route_id`, `route_decl_id`, `selected_route_rank`, `selection_rationale`, `ai4ss_model_path`, `research_question`, `model_scope`, `candidate_inquiry`, `candidate_concepts`, `candidate_causal_links`, `candidate_empirical_bridges`, `possible_data_strategy`, `possible_answer_strategy`, `study_type`, `unit_of_analysis`, `materials_available`, `materials_gap`, `registration_relevance`, `transparency_level_target`, `first_action`, `failure_signal`, `assumptions_to_disclose`, `aiss_check_status`, `next_skill_route`.
- Downstream routes: `study-design-builder`, `public-data-sources`, `research-data-builder`, `literature-matrix`, `methods-reviewer`, `academic-writing-scaffold`, `research-slides-builder`, `did-expert`, or `research-analysis-runner` when the selected route already has analysis-ready real observed data.

## Single Manuscript-Facing Boundary

AI may draft, revise, or sketch working text when AI contribution disclosure,
outlet-policy status, and accountability language are made explicit in the
artifact. The harness target is a publication-level draft PDF with those
statements present, not a hidden-AI or unsupported submission claim.

## Routing Boundaries

Use this skill before the project has a chosen route, dataset pipeline, verified literature base, model table, or writing scaffold. After a route is selected, hand off:

- Source acquisition and access verification to `public-data-sources`.
- Analysis-sample construction from acquired real observed sources to `research-data-builder`.
- Literature search, screening, or extraction to `literature-matrix`.
- Study design concretization to `study-design-builder`.
- First-pass analysis execution to `research-analysis-runner` only after a design source and analysis-ready data exist.
- Identification and result-claim validity to `methods-reviewer`, or `$did-expert` when DID/event-study is central.
- Section planning and claim slots to `academic-writing-scaffold`.
- Research decks to `research-slides-builder`.

Do not duplicate downstream validators. This skill makes the first object exist; downstream skills audit and deepen it.

## Workflow

```
Step -1: Intake only what is available
-> Capture four fields: one-sentence question or phenomenon, available materials, hard boundaries, and the one action the researcher hopes AI can do next.
-> If information is missing, infer the strongest defensible default from files, sources, and disciplinary practice; record the assumption and keep moving.

Step 0: Inventory materials
-> Inspect the file tree, notes, variable dictionaries, seed papers, data previews, or source links provided.
-> Separate usable materials, uncertain materials, unavailable materials, and confidential or off-limits materials.

Step 1: Build candidate route declarations
-> For open-ended topics, produce 2-4 `.aiss` `route` declarations, score them, and mark exactly one as the selected route in the same run.
-> Each route declaration must name the question, phenomenon, unit, real observed source acquisition path, first action, expected first output, feasibility status, failure signal, selection score, selection rationale, and next skill route.
-> Mark whether the route is registration-relevant and what transparency target it implies for materials, data, code, and reporting.
-> When the work will continue in the research-factory workflow, write each candidate directly as a `.aiss` `route` declaration and preserve the selected route identity.
-> Do not send data, literature, analysis, review, writing, slide, or revision work downstream unless `route_decl_id` and `ai4ss_model_path` are present in `.aiss`; repair the `.aiss` object if those fields are missing.
-> If the user already picked one route, still record alternatives and confirm the selected route unless another route is clearly stronger for a publication-level draft PDF.

Step 2: Define a minimum viable study
-> Choose the smallest study that can produce one checkable observation, table shell, figure shell, source matrix seed, or data feasibility result.
-> Do not jump to a full model battery, systematic review, or polished argument.

Step 3: Run or prepare one next action
-> Execute the next action when inputs are present and permitted.
-> Otherwise create the concrete downstream handoff object, command, search query, or file scaffold needed for the next skill to continue automatically.
-> Keep the action material-to-action: inspect, sample, retrieve, sketch, scaffold, or draft AI-disclosed working text through the proper downstream skill.

Step 4: Continue the relay
-> End with the selected `route_id`, `selection_rationale`, assumptions to disclose, validation status, and `next_skill_route`.
-> If the initially strongest route is infeasible, automatically select the next strongest route that can still support a publication-level draft PDF.
```

## Default Outputs

- `.ai4ss/research_model.aiss` with candidate `route` declarations, one selected route, and assumption/disclosure declarations.
- Optional author-facing chat note generated from `.aiss`, clearly marked as non-canonical.
- Runtime logs only when referenced as `.aiss` evidence artifacts.

## Script Utilities

- Run `python3 dsl/scripts/aiss.py compile .ai4ss/research_model.aiss` and `python3 dsl/scripts/aiss.py lint .ai4ss/research_model.aiss` when a route-only `.aiss` artifact is produced.
- Treat validator failures as starter artifacts, not terminal noise: record the failed command, the exact schema or import error, the fix, and the rerun result before handing off.
- If an installed validator cannot import `ai4ss_factory_contracts`, set `AI4SS_SKILLS_ROOT` to the `ai4ss-skills` source checkout and rerun; do not ignore the validation gate.

## Quality Bar

- Start from publication-level feasibility, not compliance.
- Prefer concrete `.aiss` route declarations over general advice.
- Keep the selected route small enough to start within a day while still capable of supporting a publication-level draft PDF.
- Treat data availability, source access, and variable existence as first-class findings.
- Do not select a route whose empirical chain depends on synthetic, simulated,
  hypothetical, illustrative, generated, DGP-created, random-draw,
  benchmark-calibrated, or literature-parameter-imputed data.
- Include a failure signal for every next action.
- Preserve AI-use disclosure needs in the draft PDF without making them a harness stop condition.
- Use downstream skills only after a research object exists.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [starter-workflow.md](references/starter-workflow.md) | First-loop workflow, route-declaration shape, and stop rules | Starting any zero-to-one research task |
| [minimum-viable-study.md](references/minimum-viable-study.md) | Minimum viable study patterns across descriptive, causal, text, qualitative, and mixed-method projects | Choosing the smallest credible first study |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for intake, route declarations, MVS selection, first action, and handoff | Turning a loose request into an agent task |
| [worked-example.md](references/worked-example.md) | Digital-government and firm-innovation route-declaration example | Teaching or demonstrating the skill |
