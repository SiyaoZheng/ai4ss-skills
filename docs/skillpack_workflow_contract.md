# Skillpack Workflow Contract

This contract keeps the local AI4SS skills coherent as one research workflow rather than separate helpers.

## Factory IR

The workflow contract is implemented by the `.aiss` version `0.4` DSL, compiled
through `dsl/scripts/aiss.py` into `aiss.unified_ast.v0.4`. This local contract
defines how each skill updates or mirrors that computable research object.

| object | role |
|---|---|
| `.aiss` research object | The only workflow state: route declarations, MIDA rows, automation assumptions, source spans, claims, empirical objects, couplings, attributes, concepts, causal implications, empirical bridges, artifacts, adapters, checks, diagnostics, and append-only `event` declarations |
| MIDA declaration | Seven `mida` declarations for the selected route: Model, Inquiry, Data strategy, Answer strategy, Diagnose, Redesign, Report boundary |
| Inspection files | Optional human-facing exports, logs, tables, figures, data files, or notes referenced by the `.aiss` workflow. They are not handoff contracts and cannot substitute for `.aiss` declarations. |

`research-starter` may create provisional `route` declarations without a final
model. `study-design-builder` selects a route, writes the seven `mida`
declarations, and creates or updates `research_model.aiss`. Downstream skills
must update or reference the same `.aiss` object when they add data, literature,
analysis, review, reporting, or revision work.

See `docs/ai4ss_dsl_factory_integration.md` for the full integration rule.

## State-Machine Boundary

`.aiss` is now the research-factory state-machine engine. Durable semantic
research state remains in `route`, `mida`, `decision`, source, evidence,
artifact, check, and claim declarations. Runtime observations enter as
append-only `event` declarations: skill starts, completions, failures, heartbeat
observations, watchdog recoveries, and handoff facts.

Use these commands as the canonical projection and transition interface:

```bash
python3 dsl/scripts/aiss.py state path/to/research_model.aiss
python3 dsl/scripts/aiss.py transition path/to/research_model.aiss --event '{"type":"skill_started","skill":"research-starter"}'
```

The reducer can suggest actions such as `dispatch_skill`, `repair_route`, or
`watchdog_recover`, but it does not execute skills or own processes. `goal-cli`
remains the external watchdog, timer, process-lock owner, heartbeat executor,
and recovery runner. The skillpack may emit facts and handoffs for `goal-cli`
to observe; it must not reimplement `goal-cli`.

## AI4SS Execution Gate

Research-factory skills must not execute as generic helpers that bypass the
`.aiss` research object. The factory entrypoint is always AI4SS:

1. If the project has only a rough topic or material pile, `research-starter`
   must create or update `.aiss` `route` declarations before downstream work is
   treated as a factory artifact.
2. If a route exists but no selected route plus seven MIDA declarations exists,
   `study-design-builder` must create or repair `research_model.aiss` before
   data, literature, analysis, review, writing, slides, or revision skills run
   as production workflow stages.
3. Downstream skills may inventory files and report a repair/check requirement, but they must
   not create an alternative workflow record in CSV, Markdown, chat memory, or
   an ad hoc table. Production state lives in `.aiss`.
4. Optional logs, data files, tables, figures, decks, or notes may exist only as
   evidence artifacts referenced by `.aiss` `source`, `artifact`, `empirical`,
   `observation`, `claim`, `check`, `derive`, or `decision` declarations.
   Runtime facts may be recorded as `.aiss` `event` declarations, but events do
   not replace the semantic declarations that downstream skills need.
5. If the AI4SS object is missing, invalid, or insufficient for the requested
   stage, the correct output is an automatic repair handoff with
   `next_skill_route` set to the owning factory skill such as
   `research-starter`, `study-design-builder`, `public-data-sources`,
   `research-data-builder`, or `methods-reviewer`; continuing without the AI4SS
   object is a contract violation.

## Workflow Map

| stage | scholar question | primary skill | canonical `.aiss` state | next stage |
|---|---|---|---|---|
| 0. Start | 这个研究怎么先动起来？ | `research-starter` | candidate `route` declarations plus author `decision` declarations | Design |
| 1. Design | 这个路线怎样落成可执行设计？ | `study-design-builder` | selected `route`, exactly seven `mida` declarations, author `decision` declarations, and model/check declarations | Source acquisition, literature, analysis |
| 2a. Source acquisition | 数据源从哪里来、能不能实时取到？ | `public-data-sources` | source-candidate, access-class, official-docs, request-template, live-access, license/terms, and provenance declarations for real observed public or authorized sources | Data sample, analysis |
| 2b. Data sample | 真实来源怎样变成可审计样本？ | `research-data-builder` | `source`, `artifact`, `empirical`, `observation`, `coupling`, `bridge`, `check`, and `decision` declarations for observed-data extraction, cleaning, linkage, row provenance, and row-loss evidence | Analysis, methods review |
| 2c. Literature | 文献证据是不是一手来源？ | `literature-matrix` | `paper`, `source`, `span`, `claim`, `relation`, `concept`, `causal`, `bridge`, `check`, and `decision` declarations for verified literature evidence | Design, methods review, writing scaffold |
| 3. Analysis | 第一批可检查结果怎么跑出来？ | `research-analysis-runner` | `artifact`, `adapter`, `check`, `derive`, `observation`, `claim`, and `decision` declarations linking outputs to MIDA | Figure packaging, methods review |
| 3b. Paper figures | 论文主图够不够顶刊？ | `top-journal-figures` | ggplot2 figure `artifact`, shared style profile, plotted-data `derive`/`observation`, helper-tool transparency, style-consistency/visual-integrity/vector/black-white `check`, and author `decision` declarations | Methods review, writing |
| 4. Review | 结果解释有没有说过头？ | `methods-reviewer` | diagnostic `check` declarations, redesign `decision` declarations, bounded claim links | Analysis, figures, writing, revision |
| 5a. Writing and paper package scaffold | 作者怎样写得更稳、披露得更清楚？ | `academic-writing-scaffold` | report-boundary `mida`, bounded `claim` declarations, citation-gap `decision` declarations, TOP disclosure matrix, AI-use disclosure, direct-submission status, and manuscript assembly checklist | AI-disclosed drafting |
| 5b. Slides | 已验证证据怎样讲给听众？ | `research-slides-builder` | `artifact`, bounded `claim`, source-link, privacy `check`, and presentation `decision` declarations | Author presentation |
| 5c. Revision | 返修有没有证据链？ | `reviewer-response` | reviewer-request `decision`, affected MIDA links, evidence `artifact`, and response-boundary declarations | Data, analysis, figures, writing |

## Shared Handoff Fields

Every skill should preserve these identifiers in `.aiss` declarations when
available:

| field | meaning |
|---|---|
| `route_id` | Human-readable route key such as `R1`, preserved as metadata on `.aiss` declarations |
| `route_decl_id` | Stable `.aiss` `route` declaration id from `research-starter` |
| `mida_id` | Stable `.aiss` `mida` declaration id from `study-design-builder`, when applicable |
| `decision_decl_id` | Stable `.aiss` `decision` declaration id for human-accountable choices, when applicable |
| `mida_component` | `.aiss` `mida` component touched by this artifact, when applicable |
| `synthesis_id` | Theory synthesis declaration id, when applicable |
| `rival_id` | Rival explanation decision/check id, when applicable |
| `scope_id` | Scope condition decision/check id, when applicable |
| `design_source` | Path to the design brief or decision register |
| `target_inquiry` | The declared inquiry, estimand, target quantity, construct, classification target, process-tracing claim, or synthesis question |
| `data_source` | Path to source data, derived data, or extracted source output |
| `analysis_plan_path` | Path to analysis plan, preregistration scaffold, or script plan |
| `registration_status` | Whether the study route is unregistered, registration-relevant, registered, or auto-declared for the draft package |
| `protocol_path` | Path to protocol or protocol scaffold when one exists |
| `materials_transparency_status` | Whether source materials, search protocols, instruments, or extraction materials are open, restricted, confidential, unavailable, or require author disclosure |
| `source_access_status` | Whether an observed source was verified live, queued for authorized access, rate-limited, unavailable, or replaced by another observed source |
| `row_source_provenance` | Row/cell-level source locator, extraction rule, merge lineage, or aggregate-table locator for analysis-facing data |
| `observed_data_only_status` | Whether every manuscript-facing empirical row/cell comes only from real observed public or authorized sources |
| `data_transparency_status` | Whether raw/derived observed data are open, restricted, confidential, unavailable, or require author disclosure |
| `analysis_code_transparency_status` | Whether code, scripts, notebooks, runtime, seeds, and dependencies are available and runnable |
| `reporting_transparency_status` | Whether manuscript/deck/response disclosures cover design, evidence, data, code, limits, and AI use |
| `replication_package_status` | Whether the project has a complete, partial, restricted, or repair-required replication package |
| `fair_metadata_status` | Whether data/code/materials have enough metadata, locators, checksums, and formats for reuse |
| `deviation_log_status` | Whether deviations from registration, protocol, or analysis plan are absent, declared, unresolved, or human-accountable |
| `readiness_status` | `ready`, `warn`, or `repair_required` status from `.aiss` readiness checks |
| `evidence_compile_status` | `compiled`, `needs_review`, `repair_required`, or `not_applicable` status for literature evidence in `.aiss` |
| `theory_workbench_status` | `ready_for_aiss`, `auto_resolved`, `needs_methods_review`, `repair_required`, or `not_applicable` status for theory declarations |
| `source_artifacts` | Source locators, notes, PDFs, tables, figures, logs, and other evidence files referenced by `.aiss` |
| `known_gaps` | Missing data, unresolved source, unclear design choice, or failed validation |
| `assumption_register` | Auto-selected assumptions, limits, and repair routes |
| `validation_commands` | Commands run or exact commands still needed |
| `interpretation_boundary` | What the artifact can and cannot support |
| `next_skill_route` | The next skill or `none` only when no downstream work remains |

When a stage depends on a declared `.aiss` model, preserve these identifiers in
`.aiss` metadata where applicable:

- `ai4ss_model_path`
- `model_id`
- `concept_id`
- `causal_id`
- `bridge_id`
- `ai4ss_check_status`
- `commensurability_status`

## Transparency Standard Boundary

The research factory treats current open-science transparency practices as
handoff requirements, not as optional appendix cleanup. The relevant boundary is:

```text
registration/protocol/analysis plan -> materials/data/code transparency ->
computational reproducibility -> reporting disclosure -> AI-disclosed manuscript package
```

The only manuscript-facing AI boundary in this skillpack is disclosure and
direct-submission gating. Skills may draft, revise, audit, and assemble working
manuscript or reviewer-response text. They must not present any output as
submission-ready or as having no AI involvement unless `.aiss` or linked
artifacts make AI contribution disclosure, human accountability,
outlet-policy-check status, study registration, protocol, analysis-plan,
materials, data, analytic code, reporting, deviation-log, and
replication-package status visible.

| transparency object | primary owner | downstream check |
|---|---|---|
| Study registration/protocol/analysis plan | `study-design-builder` | `methods-reviewer`; `reviewer-response` when revisions change the plan |
| Public data source access and source-status ledger | `public-data-sources` | `research-data-builder`; `research-analysis-runner`; `methods-reviewer` |
| Literature search strategy and source-status ledger | `literature-matrix` | `academic-writing-scaffold`; `methods-reviewer` |
| Observed data lineage, sample flow, and FAIR metadata | `research-data-builder` | `research-analysis-runner`; `methods-reviewer` |
| Analytic code, runtime, seeds, and computational reproducibility | `research-analysis-runner` | `methods-reviewer` |
| Publication-facing R/ggplot2 figure code, shared style profile, helper-tool transparency, vector exports, captions, and source notes | `top-journal-figures` | `methods-reviewer`; `academic-writing-scaffold` |
| Reporting disclosure matrix and AI-disclosed manuscript assembly checklist | `academic-writing-scaffold` | `reviewer-response`; `methods-reviewer` |
| Revision transparency and deviation log | `reviewer-response` | `methods-reviewer`; affected production skill |

All manuscript or response working text produced before the gate is
`submission_ineligible_ai_assisted_working_text`. The gate passes only when the
package records `ai_contribution_disclosure`, `human_accountability_status`,
`submission_policy_check_status`, and `direct_submission_status`. This replaces
the prior blanket ban on AI-assisted manuscript, theory, or response drafting.

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
| `Report` | Bounded claim declarations, source map, AI-use ledger, AI contribution disclosure, direct-submission status, assumption register, and communication boundary |

## Theory Workbench Contract

The shared theory engine is implemented as a reusable workflow layer across
`literature-matrix`, `study-design-builder`, `methods-reviewer`, and
`academic-writing-scaffold`. It reuses existing contracts:

- Route/status checks live in `scripts/ai4ss_factory_contracts/workflow.py`.
- Model output is compiled through `dsl/scripts/compile_evidence.py`.
- Model validity is checked through `scripts/validate_ai4ss_model.py`.
- Rival, scope, mechanism weakness, and overclaim are reviewed through `.aiss`
  `check` and `decision` declarations.
- Author-facing theory review uses the single disclosure/submission gate when
  working theory prose is drafted.

## Common Skill Requirements

Each local skill must have:

- `## Methodology Foundation`
- `## Workflow Contract`
- `## Routing Boundaries`
- a concrete output section: `## Default Outputs`, `## Required Outputs`, or `## Output Shape`
- `## Script Utilities`
- `## Reference Files`

The workflow contract is intentionally short. Detailed `.aiss` declaration
patterns belong in skill-local `references/` files and deterministic checks
belong in `dsl/scripts/aiss.py` or `scripts/validate_ai4ss_model.py`. A skill is
incomplete if it only cites methods sources but does not state its role in the
design spine.

## Gap Decisions From Round 2

Two gaps were found after adding `research-starter`:

- Design gap: no skill owned the move from candidate route declarations to unit, constructs, comparison, evidence needs, and first analysis plan. Added `study-design-builder`.
- Execution gap: no skill owned the move from design plus analysis-ready data to first-pass outputs and logs. Added `research-analysis-runner`; it now requires `.aiss` readiness checks before execution.

These are production skills. They do not replace the second-order audit skills.

## Teaching Rule

Teach the workflow as a relay:

```text
start -> design -> source acquisition -> observed data sample -> literature evidence -> analysis -> figures -> review -> writing/slides/revision
```

Do not teach provenance as the first action. Teach provenance as the audit discipline that becomes useful once a research object exists.
