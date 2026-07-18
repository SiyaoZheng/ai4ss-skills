# Skillpack Workflow Contract

This contract keeps the local AI4SS skills coherent as one research workflow rather than separate helpers.

## Factory IR

The workflow contract is implemented by the `.aiss` version `0.4` DSL, compiled
through `dsl/scripts/aiss.py` into `aiss.unified_ast.v0.4`. This local contract
defines how each skill updates or mirrors that computable research object.

| object | role |
|---|---|
| `.aiss` research object | Unified computable IR: route declarations, MIDA rows, required gates, source spans, claims, empirical objects, couplings, attributes, concepts, causal implications, empirical bridges, checks, and derived diagnostics |
| MIDA declaration | Seven `mida` declarations for the selected route: Model, Inquiry, Data strategy, Answer strategy, Diagnose, Redesign, Report boundary |
| Skill sidecars | Human-readable or validator-friendly projections: route cards, design declarations, DDI metadata, cleaning contracts, sample flow, literature matrix, theory workbench sidecars, compiled literature/theory evidence, analysis readiness check, analysis manifest, claim ledger |

`research-starter` may create provisional `route` declarations without a final
model. `study-design-builder` selects a route, writes the seven `mida`
declarations, and creates or updates `research_model.aiss` when conceptual or
causal structure matters. Downstream skills should preserve model identifiers
and source-span grounding when an artifact depends on a declared route, MIDA
component, concept, causal implication, empirical bridge, or claim.

See `docs/ai4ss_dsl_factory_integration.md` for the full integration rule.

## Workflow Map

| stage | scholar question | primary skill | canonical artifact | next stage |
|---|---|---|---|---|
| 0. Start | 这个研究怎么先动起来？ | `research-starter` | `.aiss` `route` declarations, mirrored by `research_starter_packet.md` and `research_route_cards.csv` | Design |
| 1. Design | 这个路线怎样落成可执行设计？ | `study-design-builder` | selected `.aiss` `route`, seven `mida` declarations, `decision` declarations, `research_model.aiss`, `ai4ss_check_report.txt` | Source acquisition, data, literature, analysis |
| 2a. Source acquisition | 真实观测证据对象从哪里来？ | `public-data-sources` | ranked source route, access class, request template, live-access evidence, cached bounded source artifact, `source_artifact_path`, checksum, provenance | Data, design redesign, methods review |
| 2b. Data | 数据怎么来的，样本怎么变的？ | `research-data-builder` | derived data, `sample_flow.csv`, `merge_audit.csv`, `variable_provenance.csv`; for survey cleaning: `ddi-metadata.yaml`, `cleaning_contract`, execution audit | Analysis, methods review |
| 2c. Literature | 文献证据是不是一手来源？ | `literature-matrix` | `literature_candidate_discovery.csv`, `literature_matrix.csv`, optional theory workbench (`literature_theory_synthesis.csv`, `theory_rival_map.csv`, `theory_scope_map.csv`, `theory_evidence.md`), optional compiled literature/theory `.aiss` evidence | Design, methods review, writing scaffold |
| 3. Analysis | 第一批可检查结果怎么跑出来？ | `research-analysis-runner` | `analysis_readiness_check.csv`, scripts, tables, figures, logs, `analysis_run_manifest.csv` | Methods review |
| 4. Figures | 可视证据是否能进论文？ | `top-journal-figures` | figure spec, R/ggplot2 plotting code, `figure_path`, source note, visual-integrity check | Methods review, writing |
| 5. Review | 结果解释有没有说过头？ | `methods-reviewer` | issue table, recommended checks, required gates | Analysis, figures, writing, revision |
| 6a. Working article | 已完成的研究对象怎样形成可读成果？ | `academic-writing-scaffold` plus the runtime article/PDF harness | paper-section artifacts, figure/table bundle, references, full paper source, working article/PDF artifact | Completion |
| 6b. Slides | 已验证证据怎样讲给听众？ | `research-slides-builder` | slide map, source map, evidence gaps | Author presentation |
| 6c. Revision | 返修有没有证据链？ | `reviewer-response` | revision matrix, revision plan, response scaffold | Data, analysis, writing |

Source acquisition is observed public-source acquisition or authorized-source
acquisition; it is not synthetic-data creation.

## State Machine Contract

The research factory is a state machine, not a best-effort checklist. Its
deterministic core lives in:

- `scripts/ai4ss_factory_contracts/workflow.py` for route/status transitions.
- `scripts/ai4ss_factory_contracts/sidecars.py` for sidecar projections of the
  `.aiss` object.
- `dsl/scripts/aiss.py transition <research_model.aiss>` for the executable
  paper-artifact state: current full-paper gaps, the next paper artifact to
  write or verify, evidence gates, and blocking reasons from the current
  `.aiss` state. `required_artifacts` identifies gate owners and evidence
  needed for blocked paper artifacts.
- `scripts/audit_skill_handoffs.py` for cross-skill relay continuity.
- `scripts/run_skill_handoff_audit_fixtures.py` for deterministic pass/fail
  state-machine fixtures.

The `.aiss` declarations map to workflow contexts:

| `.aiss` declaration | state-machine context | required behavior |
|---|---|---|
| `route` | `research_routes` | a selected route must name a downstream skill, not stop in prose |
| `mida` | `study_design_declaration` | gate statuses must route to the owning skill or to `last_skill` with a redesign reason |
| `decision` | `design_decisions` | harness-owned decisions must preserve the selected route and next route |
| `event` | `event` | runtime events may record route transitions, but cannot replace `.aiss` state |

The fixture `docs/evals/factory-relay/fixtures/valid_relay.aiss` is the minimal
known-good relay. It must pass:

```bash
PYTHONPATH=scripts python3 scripts/test_factory_contracts.py
PYTHONPATH=scripts python3 scripts/run_skill_handoff_audit_fixtures.py
```

The deterministic relay audit also rejects parallel Markdown/CSV/JSON workflow
state, missing report boundaries, misrouted repair rows, dropped empirical
artifact links, missing downstream consumers, and synthetic/demo fallback
analysis.

## Shared Handoff Fields

Every skill should preserve these fields when available:

| field | meaning |
|---|---|
| `route_id` | Human-readable route key such as `R1`, preserved across sidecars |
| `route_decl_id` | Stable `.aiss` `route` declaration id from `research-starter` |
| `mida_id` | Stable `.aiss` `mida` declaration id from `study-design-builder`, when applicable |
| `decision_decl_id` | Stable `.aiss` `decision` declaration id for workflow-gated choices, when applicable |
| `mida_component` | `.aiss` `mida` component touched by this artifact, when applicable |
| `synthesis_id` | Theory synthesis row id from `literature_theory_synthesis.csv`, when applicable |
| `rival_id` | Rival explanation row id from `theory_rival_map.csv`, when applicable |
| `scope_id` | Scope condition row id from `theory_scope_map.csv`, when applicable |
| `design_source` | Path to the design brief or decision register |
| `target_inquiry` | The declared inquiry, estimand, target quantity, construct, classification target, process-tracing claim, or synthesis question |
| `source_name` | Name of the selected real observed public or authorized source |
| `source_access_status` | Whether the source is live-accessible, cached, queued for key/permission, failed, or requires redesign |
| `access_class` | `public_no_secret`, `free_key_required`, or `download_ingest_only` |
| `request_template` | Safe reproducible API request, package call, or download command |
| `source_artifact_path` | Path to the cached bounded source artifact handed to data construction |
| `source_artifact_checksum` | Checksum for the cached source artifact when available |
| `observed_data_only_status` | Gate stating that downstream empirical rows come from real observed public or authorized sources |
| `row_source_provenance` | Row/cell/document provenance sufficient for data construction and audit |
| `data_source` | Path to source data, derived data, or extracted source output |
| `analysis_plan_path` | Path to analysis plan, preregistration scaffold, or script plan |
| `readiness_status` | `ready`, `warn`, or `blocked` result from `analysis_readiness_check.csv` |
| `evidence_compile_status` | `compiled`, `needs_review`, `blocked`, or `not_applicable` status for literature evidence to `.aiss` compilation |
| `theory_workbench_status` | `ready_for_aiss`, `needs_redesign`, `needs_methods_review`, `blocked`, or `not_applicable` status for theory sidecars |
| `source_artifacts` | Literature matrix, source ledger, notes, PDFs, tables, figures, logs |
| `known_gaps` | Missing data, unresolved source, unclear design choice, or failed validation |
| `required_gates` | Gate conditions that must be resolved by redesign, source checks, data checks, methods review, or controller routing |
| `validation_commands` | Commands run or exact commands still needed |
| `interpretation_boundary` | What the artifact can and cannot support |
| `next_skill_route` | The next skill or `last_skill` / `none` |

`last_skill` is a bounded repair-loop edge, not a stop state and not a final
answer. It means the current skill has reached a boundary that must be returned
to the previous skill, caller, or workflow controller with concrete redesign,
source-gate, data-gate, or required-gate reasons. It never delegates outside
workflow control, and it is not permission to draft final manuscript claims or
final reviewer-response prose.

A row that routes to `last_skill` must carry concrete reason fields such as
`stop_reason`, `failure_signal`, `known_gaps`, `required_gate`,
`diagnosand_or_gate`, or `redesign_option`. The receiving layer must use those
reasons to redesign, source-gate, data-gate, or method-review until the run
reaches a feasible current inquiry. A completed harness run must not end with
`last_skill`, `blocked`, `PENDING`, or "no gates passed" as its result.

## No-Dead-End Completion Invariant

Every harness run must complete one honest research path. If the original
question cannot be answered with available evidence, the workflow must narrow
the inquiry, reduce claim strength, change the data strategy, change the answer
strategy, or abandon the original route in favor of a feasible neighboring
route. The result is still a completed research object; the stronger original
claim becomes an upgrade gate, not the run outcome.

Use these gate classes:

| gate class | meaning | allowed final status |
|---|---|---|
| `current_run_gate` | Required for the claim actually made in this run | `passed`, `redesigned`, or `scoped_out` |
| `upgrade_gate` | Required only for a stronger future claim or broader route | `queued` |

The controller must keep looping while any `current_run_gate` is unresolved. It
may finish only when the current paper-section artifacts, analysis object,
report boundary, figure/table bundle, references, full paper source, and full
paper artifact are internally consistent. Claim ledgers and AI-use ledgers can
remain required evidence or disclosure gates, but they are not the state
machine's terminal object. The final artifact for a completed run is the full
paper, not a loose scaffold or partial handoff packet. In validator terms, the
full paper is the working article/PDF artifact, and completion means that
artifact has been produced.

Fabricated, simulation-only, toy, placeholder, or demo-only material must not
be used as a fallback analysis. If real analysis-ready data are unavailable,
redesign the answer strategy to a non-estimating analysis of real available
artifacts such as verified source records, extraction tables, design
diagnostics, claim ledgers, or method-review issue tables. Diagnostic
simulation is allowed only when explicitly part of a declared design diagnostic
and not presented as the substantive analysis.

When a stage depends on a declared `.aiss` model, preserve these optional fields
in sidecars where applicable:

- `ai4ss_model_path`
- `model_id`
- `concept_id`
- `causal_id`
- `bridge_id`
- `ai4ss_check_status`
- `commensurability_status`

## Methodology Spine

The workflow is not a sequence of agent conveniences. It is a research-design relay:

```text
Declare MIDA -> Diagnose -> Redesign -> Report with bounded claims
```

Use `docs/methodology_foundations.md` as the canonical explanation and `docs/methodology_source_matrix.csv` as the validator-readable map.

| design element | minimum meaning |
|---|---|
| `Model` | Units, constructs, mechanisms, assumptions, scope conditions |
| `Inquiry` | Causal estimand, descriptive quantity, measurement target, classification target, process-tracing claim, or synthesis question |
| `Data strategy` | Sampling, source selection, measurement, extraction, linkage, missingness, and source-screening rules |
| `Answer strategy` | Estimator, coding rule, synthesis rule, diagnostic comparison, table/figure shell, or qualitative inference procedure |
| `Diagnose` | Bias, precision, power, measurement risk, source-status risk, row loss, reproducibility, and claim-support mismatch |
| `Redesign` | Smaller first loop, revised measure, added source, changed estimator, stronger comparison, or abandoned route |
| `Report` | Claim ledger, source map, AI-use ledger, required gate point, and communication boundary |

## Theory Workbench Contract

The shared theory engine is implemented as a reusable workflow layer across
`literature-matrix`, `study-design-builder`, `methods-reviewer`, and
`academic-writing-scaffold`. It reuses existing contracts:

- Sidecar fields live in `scripts/ai4ss_factory_contracts/sidecars.py`.
- Route/status checks live in `scripts/ai4ss_factory_contracts/workflow.py`.
- Model output is compiled through `dsl/scripts/compile_evidence.py`.
- Model validity is checked through `scripts/validate_ai4ss_model.py`.
- Rival, scope, mechanism weakness, and overclaim are reviewed through the
  existing methods issue table.
- Author-facing theory review uses the Gate Workbench boundary; final theory
  prose remains author-written.

## Common Skill Requirements

Each local skill must have:

- `## Methodology Foundation`
- `## Workflow Contract`
- `## Routing Boundaries`
- a concrete output section: `## Default Outputs`, `## Required Outputs`, or `## Output Shape`
- `## Script Utilities`
- `## Reference Files`

The workflow contract is intentionally short. Detailed schemas belong in skill-local `references/` files and deterministic checks belong in skill-local `scripts/`. A skill is incomplete if it only cites methods sources but does not state its role in the design spine.

## Gap Decisions From Round 2

Two gaps were found after adding `research-starter`:

- Design gap: no skill owned the move from route cards to unit, constructs, comparison, evidence needs, and first analysis plan. Added `study-design-builder`.
- Execution gap: no skill owned the move from design plus analysis-ready data to first-pass outputs, logs, and result manifests. Added `research-analysis-runner`; it now requires `analysis_readiness_check.csv` before execution.

These are production skills. They do not replace the second-order audit skills.

## Teaching Rule

Teach the workflow as a relay:

```text
start -> design -> data/literature -> analysis -> review -> writing/slides/revision
```

Do not teach provenance as the first action. Teach provenance as the audit discipline that becomes useful once a research object exists.
