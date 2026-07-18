# Skillpack Gap Map

This note records the multi-round reassessment of the local AI4SS skillpack.

## Round 1: Consistency Problem

Finding: the skills had strong local boundaries but weak shared interfaces. Each skill knew its own artifact, but the pack did not have a shared contract for `route_id`, upstream inputs, downstream routes, stop reasons, required gates, or interpretation boundaries.

Change:

- Added a `Workflow Contract` section to each local skill.
- Added `docs/skillpack_workflow_contract.md`.
- Added `scripts/validate_skillpack_workflow.py`.

## Round 2: Production Gaps

Finding: after `research-starter`, the first-order production layer still had two missing handoffs.

| gap | why it matters | added skill |
|---|---|---|
| Route to design | Ordinary scholars need help turning a possible route into unit, constructs, comparison, evidence needs, and first analysis plan | `study-design-builder` |
| Design/data to outputs | Existing skills could build data and audit methods, but none owned first-pass tables, figures, logs, and result manifests | `research-analysis-runner` |

## Round 3: Methodology Spine Gap

Finding: a coherent workflow is still weak if its parts are grounded only by scattered source anchors. The missing layer was a shared research-design grammar that tells every skill what kind of methodological object it owns.

Change:

- Reframed methodology foundations around `Declare MIDA -> Diagnose -> Redesign -> Report with bounded claims`.
- Added `## Methodology Foundation` to every local skill.
- Rebuilt `docs/methodology_source_matrix.csv` so it records framework role, MIDA component, declaration fields, diagnosands/gates, canonical artifacts, status, and remaining gap.
- Updated validators so workflow consistency now requires methodology roles, not only artifact handoffs.

Design decision:

- `estimand` is important but not sufficient. It belongs inside `Inquiry`. Every causal estimand must be linked to Model, Data strategy, Answer strategy, and Diagnose gates; non-causal work must declare its target quantity, construct, classification target, process-tracing claim, or synthesis question with the same discipline.

## Round 4: Methodology Enforcement Gap

Finding: the shared methodology spine was present in documentation and `SKILL.md` files, but several sidecar schemas still allowed the workflow to lose the declared design object. A validator PASS could mean that prose named MIDA without proving that actual artifacts carried MIDA fields.

Change:

- Added `study_design_declaration.csv` as a MIDA declaration projection for `study-design-builder`.
- Upgraded route cards into pre-declarations with `model_scope`, `candidate_inquiry`, `possible_data_strategy`, and `possible_answer_strategy`.
- Threaded `design_source` and `target_inquiry` through data, literature, analysis, methods, writing, slides, and revision sidecars where those artifacts depend on a design.
- Added `mida_component`, `mida_element_affected`, `interpretation_boundary`, `diagnosed_limit`, `sample_or_scope`, `uncertainty_or_caveat`, and privacy/boundary fields to downstream contracts where needed.
- Upgraded `scripts/validate_methodology_foundations.py` so it checks skill-local schema references, validator scripts, and valid examples, not only the methodology matrix.

Decision:

- The pack is now methodology-enforcing for the workshop's cross-skill workflow. It is still not a universal specialist-methods system; DID stays delegated to `$did-expert`, and IV/RD/RCT/survey/network/spatial/ML should become specialist skills only when course cases require them.

## Round 5: Explicit DSL Gap

Finding: local workflow and MIDA sidecars were being treated as if they were the
factory language. That missed the explicit `.aiss` DSL: a parsable,
source-grounded research language for spans, claims, empirical objects,
couplings, attributes, concepts, theta rules, causal implications, empirical
bridges, checks, model diagnostics, and deterministic diffs.

Change:

- Added `docs/ai4ss_dsl_factory_integration.md`.
- Reframed `docs/skillpack_workflow_contract.md` around three layers:
  MIDA declaration, unified `.aiss` v0.4 IR, and skill-local sidecars.
- Marked `study-design-builder` as natural owner optional
  `research_model.aiss` and `ai4ss_check_report.txt`.
- Marked `research-data-builder` as route into `ai4ss-skills`
  `codebook-parse`, `cleaning-contract`, and `cleaning-execute` when survey
  cleaning is the data bottleneck.

Decision:

- Do not invent a new `research_job.yaml` as central language. If factory
  orchestration metadata is needed, it should point to `research_model.aiss`,
  MIDA declarations, DDI/cleaning contracts, analysis manifests, and claim
  ledgers rather than replacing them.
- Do not maintain separate PaperAST and research-model DSLs. Version `0.4`
  fuses source/span grounding and research-model declarations into one
  `aiss.unified_ast.v0.4`.

Closed in the hardening pass:

- Added `scripts/validate_ai4ss_model.py`, which requires `.aiss` v0.4 files
  and runs `aiss.py compile`, `aiss.py lint`, and `aiss.py run`.
- Added `docs/examples/research_model.aiss` as a unified local fixture.
- Extended `study_design_declaration.csv`, data audits, literature matrices,
  analysis manifests, methods issue tables, and claim ledgers with
  `ai4ss_model_path`, model ids, `ai4ss_check_status`, and where relevant
  `commensurability_status`.
- Upgraded workflow and methodology validators so a PASS requires `.aiss`
  handoff terms in actual schemas, scripts, and examples.
- Closed the regression-readiness gap by adding `analysis_readiness_check.csv`
  and `scripts/validate_analysis_readiness.py`. The analysis runner now must
  validate cleaned data or extracted evidence against the declared analysis
  plan, required variables, sample/audit sidecars, row counts, and `.aiss`
  bridge alignment before execution.
- Closed the evidence compiler integration gap by adding literature-matrix
  fields for `evidence_table_path`, `compiled_ai4ss_path`, and
  `evidence_compile_status`, plus `validate_literature_evidence_compile.py`.
  The validator recompiles evidence markdown through `compile_evidence.py`,
  compares the saved `.aiss` output byte-for-byte, and validates the result
  through `aiss.py compile/lint`.

Factory-level evaluation closure:

- Added `scripts/run_factory_level_eval.py`.
- Added `docs/factory_level_eval/` with protocol, grader brief, blinded
  packets, private mapping, gate matrix, human grading sheet, rule-based scores,
  and unblinded report.
- The package now tests the whole rough-topic -> `.aiss` route declarations ->
  `.aiss` MIDA declarations -> `.aiss` model/check -> literature/data gates ->
  analysis readiness -> analysis manifest -> bounded-claim handoff chain as a
  first-order autonomous research factory task.
- Limit: this closes the deterministic structural-evaluation gap, not the
  stronger live independent field-evaluation gap.

## Round 6: Workflow DSL Fusion

Finding: route cards and MIDA declarations were still partly treated as
sidecar-level workflow objects, while `.aiss` was treated as a later
research-model attachment. Codex appserver tests confirmed the stage boundary:
`research-starter` is the blank-slate entry skill and may create route-only
candidate `.aiss` declarations when durable state is useful; `study-design-builder`
is not a blank-slate entry skill and should only promote an existing route to a
selected route with seven MIDA declarations. See
`docs/appserver_behavior_tests.md`.

Change:

- Made `route`, `mida`, and `decision` first-class `.aiss` v0.4 declarations.
- Upgraded `research-starter` so durable route cards mirror `.aiss` `route`
  declarations through `route_decl_id`.
- Upgraded `study-design-builder` so selected routes own seven `.aiss` `mida`
  declarations through `mida_id` and workflow-gated choices through
  `decision_decl_id`.
- Reframed CSV/Markdown sidecars as projections of the unified `.aiss`
  workflow object, not a second workflow DSL.

Decision:

- There is one local workflow DSL: `.aiss` v0.4. Sidecars remain useful for
  humans, classrooms, and validators, but they must point back to stable `.aiss`
  declarations when they represent route, MIDA, or decision state.

## Current Skillpack

| layer | skill | owns | must not own |
|---|---|---|---|
| Production | `research-starter` | `.aiss` route declarations, route-card projections, and minimum viable study | final prose or validity claims |
| Production | `study-design-builder` | selected `.aiss` route, MIDA declarations, design brief, and decision register | final identification judgment |
| Production | `research-data-builder` | data pipeline and provenance | research design choice |
| Production | `literature-matrix` | source discovery and extraction | literature review prose |
| Production | `research-analysis-runner` | first-pass outputs and manifests | interpretation or result selection |
| Audit | `methods-reviewer` | method/result/claim issue table | first execution as default |
| Scaffold | `academic-writing-scaffold` | claim ledger and author writing scaffold | manuscript prose |
| Scaffold | `research-slides-builder` | slide map and evidence-source mapping | new research findings |
| Revision | `reviewer-response` | revision matrix and response scaffold | final response prose |

## Remaining Watchlist

- Ethics/confidentiality may eventually need its own skill if workshop materials include interviews, private reviewer reports, or restricted administrative data.
- Qualitative/interview analysis may eventually need its own skill if examples move beyond source matrices and coding schemas.
- A stronger live factory evaluation should replace deterministic packets with independently generated live outputs, independent human expert graders, and inter-rater reliability before unblinding.
- Full design simulation is not yet built into the local skills. DeclareDesign-style Monte Carlo diagnosis remains an advanced option rather than the default classroom path.
- Specialist methods beyond DID, including IV, RD, RCT, survey, network, spatial, and ML evaluation, should become specialist skills only when workshop cases require them.
