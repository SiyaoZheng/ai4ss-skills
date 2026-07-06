# Skillpack Gap Map

This note records the multi-round reassessment of the local AI4SS skillpack.

## Round 1: Consistency Problem

Finding: the skills had strong local boundaries but weak shared interfaces. Each skill knew its own artifact, but the pack did not have a shared contract for route ids, upstream inputs, downstream routes, continuation plans, automation assumptions, or interpretation boundaries.

Change:

- Added a `Workflow Contract` section to each local skill.
- Added `docs/skillpack_workflow_contract.md`.
- Added `scripts/validate_skillpack_workflow.py`.

## Round 2: Production Gaps

Finding: after `research-starter`, the first-order production layer still had two missing handoffs.

| gap | why it matters | added skill |
|---|---|---|
| Route to design | Ordinary scholars need help turning a possible route into unit, constructs, comparison, evidence needs, and first analysis plan | `study-design-builder` |
| Source acquisition to sample | Data need a separate real observed source access gate before analysis-sample construction | `public-data-sources` |
| Design/data to outputs | Existing skills could build data and audit methods, but none owned first-pass tables, figures, logs, and result artifacts | `research-analysis-runner` |

## Round 3: Methodology Spine Gap

Finding: a coherent workflow is weak if its parts are grounded only by scattered source anchors. The missing layer was a shared research-design grammar that tells every skill what kind of methodological object it owns.

Change:

- Reframed methodology foundations around `Declare MIDA -> Diagnose -> Redesign -> Report with bounded claims`.
- Added `## Methodology Foundation` to every local skill.
- Rebuilt `docs/methodology_source_matrix.csv` so it records framework role, MIDA component, declaration fields, diagnosands/gates, canonical `.aiss` artifacts, status, and remaining gap.
- Updated validators so workflow consistency now requires methodology roles, not only artifact handoffs.

Decision:

- `estimand` is important but not sufficient. It belongs inside `Inquiry`. Every causal estimand must be linked to Model, Data strategy, Answer strategy, and Diagnose gates; non-causal work must declare its target quantity, construct, classification target, process-tracing claim, or synthesis question with the same discipline.

## Round 4: Methodology Enforcement Gap

Finding: the shared methodology spine was present in documentation and `SKILL.md` files, but the workflow still needed a durable design object that carried MIDA fields across skills.

Change:

- Made `.aiss` route, MIDA, and decision declarations the durable workflow object.
- Threaded `design_source`, `target_inquiry`, `mida_component`, `mida_element_affected`, `interpretation_boundary`, `diagnosed_limit`, sample/scope, uncertainty, privacy, and boundary fields through `.aiss` declarations where downstream artifacts depend on a design.
- Upgraded `scripts/validate_methodology_foundations.py` so it checks the methodology matrix and skill entrypoints for `.aiss` declaration continuity.

Decision:

- The pack is methodology-enforcing for the workshop's cross-skill workflow. It is still not a universal specialist-methods system; DID stays delegated to `$did-expert`, and IV/RD/RCT/survey/network/spatial/ML should become specialist skills only when course cases require them.

## Round 5: Explicit DSL Gap

Finding: local workflow and MIDA declarations were being treated as prose conventions. That missed the explicit `.aiss` DSL: a parsable, source-grounded research language for spans, claims, empirical objects, couplings, attributes, concepts, theta rules, causal implications, empirical bridges, checks, model diagnostics, and deterministic diffs.

Change:

- Added `docs/ai4ss_dsl_factory_integration.md`.
- Reframed `docs/skillpack_workflow_contract.md` around `.aiss` v0.4 as the unified workflow, evidence, and model IR.
- Marked `study-design-builder` as the owner of `research_model.aiss` and `ai4ss_check_report.txt`.
- Marked `research-data-builder` as the route into `ai4ss-skills` `codebook-parse`, `cleaning-contract`, and `cleaning-execute` when survey cleaning is the data bottleneck.

Decision:

- Do not invent a new central orchestration file. If metadata is needed, it should point to `research_model.aiss`, MIDA declarations, DDI/cleaning contracts, analysis artifacts, and bounded claim declarations rather than replacing them.
- Do not maintain separate PaperAST and research-model DSLs. Version `0.4` fuses source/span grounding and research-model declarations into one `aiss.unified_ast.v0.4`.

Closed in the hardening pass:

- Added `scripts/validate_ai4ss_model.py`, which requires `.aiss` v0.4 files and runs `aiss.py compile`, `aiss.py lint`, and `aiss.py run`.
- Added `docs/examples/research_model.aiss` as a unified local fixture.
- Upgraded workflow and methodology validators so a PASS requires `.aiss` handoff terms in actual skill entrypoints and methodology documentation.
- Closed the readiness gap by making analysis readiness a `.aiss` `check` layer.
- Closed the evidence integration gap by requiring literature evidence that changes the model to become `.aiss` declarations or deterministic `.aiss` fragments.

Factory-level evaluation closure:

- Added `scripts/run_factory_level_eval.py`.
- Added `docs/factory_level_eval/` with protocol, grader brief, blinded packets, private mapping, gate matrix, human grading sheet, LLM-as-judge prompts, judge-score sheet, and unblinded report.
- The package now tests the rough-topic -> `.aiss` route declarations -> `.aiss` MIDA declarations -> `.aiss` model/check -> observed public-source acquisition -> observed-data sample construction/check -> literature evidence gates -> `.aiss` analysis readiness -> `.aiss` analysis artifacts -> bounded-claim handoff chain as a first-order autonomous research factory task.
- Limit: this closes the structural packet-and-judge-rubric gap, not the stronger live independent field-evaluation gap.

## Round 6: Workflow DSL Fusion

Finding: route and MIDA declarations were still partly treated as external workflow objects, while `.aiss` was treated as a later research-model attachment. Codex appserver tests confirmed the stage boundary: `research-starter` is the blank-slate entry skill and may create route-only candidate `.aiss` declarations when durable state is useful; `study-design-builder` is not a blank-slate entry skill and should only promote an existing route to a selected route with seven MIDA declarations. See `docs/appserver_behavior_tests.md`.

Change:

- Made `route`, `mida`, and `decision` first-class `.aiss` v0.4 declarations.
- Upgraded `research-starter` so durable route state is stored as `.aiss` `route` declarations through `route_decl_id`.
- Upgraded `study-design-builder` so selected routes own seven `.aiss` `mida` declarations through `mida_id` and human-accountable choices through `decision_decl_id`.
- Reframed CSV and derived Markdown outputs as non-contract projections, not a workflow DSL.

Decision:

- There is one local workflow DSL: `.aiss` v0.4. External notes, logs, data files, tables, figures, decks, and reports may exist as evidence artifacts, but they must point back to stable `.aiss` declarations when they represent route, MIDA, decision, evidence, analysis, or claim state.

## Current Skillpack

| layer | skill | owns | must not own |
|---|---|---|---|
| Production | `research-starter` | `.aiss` route declarations and minimum viable study | validity claims or no-AI submission status |
| Production | `study-design-builder` | selected `.aiss` route, MIDA declarations, design decisions, and checks | final identification judgment |
| Production | `public-data-sources` | real observed source acquisition, access status, official docs, request templates, and provenance | analysis-sample cleaning or estimation |
| Production | `research-data-builder` | observed-data sample pipeline, row provenance, and `.aiss` data declarations | source acquisition or research design choice |
| Production | `literature-matrix` | source discovery, extraction, and `.aiss` evidence declarations | undisclosed no-AI literature-review status |
| Production | `research-analysis-runner` | first-pass outputs and `.aiss` analysis artifacts | interpretation or result selection |
| Production | `top-journal-figures` | final ggplot2 paper figures, shared style profile, helper-tool transparency, vector exports, and visual-integrity checks | estimation, source acquisition, or manuscript prose |
| Audit | `methods-reviewer` | diagnostic checks and redesign decisions | first execution as default |
| Scaffold | `academic-writing-scaffold` | bounded claim slots, AI-disclosed working prose, and manuscript package gate | hidden-AI submission-ready prose |
| Scaffold | `research-slides-builder` | presentation artifacts and evidence-source mapping | new research findings |
| Revision | `reviewer-response` | reviewer-request decisions, response-boundary checks, and AI-disclosed response working text | hidden-AI submission-ready response |

## Round 7: End-to-Paper Transparency Boundary

Finding: the factory covered the research-state chain well, but the final paper
boundary was too implicit. The older boundary over-relied on bans against
AI-assisted drafting, while the ecosystem did not strongly name the AI-disclosed
submission package:
registration/protocol/analysis plan, materials/data/code transparency,
computational reproducibility, reporting disclosure, deviation log, and
replication-package status.

Change:

- Added route contexts for `registration_plan`, `transparency_package`,
  `reporting_package`, and `revision_package`.
- Extended shared handoff fields with registration, protocol, analysis-plan,
  materials/data/code/reporting transparency, FAIR metadata, deviation-log, and
  replication-package status.
- Reframed `academic-writing-scaffold` as the owner of manuscript assembly
  status, disclosure matrices, AI contribution disclosure, human accountability
  status, direct-submission status, and outlet-policy check status.
- Made `study-design-builder`, `research-data-builder`,
  `research-analysis-runner`, `methods-reviewer`, and `reviewer-response`
  explicitly preserve the transparency fields they own.

Decision:

- The skillpack has one manuscript-facing AI boundary: working manuscript or
  reviewer-response text may be AI-assisted, but it is
  `submission_ineligible_ai_assisted_working_text` until AI involvement,
  human accountability, and outlet-policy checks are explicit. Do not
  reintroduce blanket bans on AI drafting.

## Remaining Watchlist

- Ethics/confidentiality may eventually need its own skill if workshop materials include interviews, private reviewer reports, or restricted administrative data.
- Qualitative/interview analysis may eventually need its own skill if examples move beyond source matrices and coding schemas.
- A stronger live factory evaluation should replace generated packets with independently generated live outputs, independent LLM/human expert graders, and inter-rater reliability before unblinding.
- Full design simulation is not yet built into the local skills. DeclareDesign-style Monte Carlo diagnosis remains an advanced option rather than the default classroom path.
- Specialist methods beyond DID, including IV, RD, RCT, survey, network, spatial, and ML evaluation, should become specialist skills only when workshop cases require them.
