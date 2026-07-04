# Skillpack Workflow Contract

This contract keeps the local AI4SS skills coherent as one research workflow rather than separate helpers.

## Factory IR

The workflow contract is implemented by the `.aiss` version `0.4` DSL, compiled
through `dsl/scripts/aiss.py` into `aiss.unified_ast.v0.4`. This local contract
defines how each skill updates or mirrors that computable research object.

| object | role |
|---|---|
| `.aiss` research object | Unified computable IR: route declarations, MIDA rows, author decisions, source spans, claims, empirical objects, couplings, attributes, concepts, causal implications, empirical bridges, checks, and derived diagnostics |
| MIDA declaration | Seven `mida` declarations for the selected route: Model, Inquiry, Data strategy, Answer strategy, Diagnose, Redesign, Report boundary |
| Skill sidecars | Human-readable or validator-friendly projections: route cards, design declarations, DDI metadata, cleaning contracts, sample flow, literature matrix, compiled literature evidence, analysis readiness check, analysis manifest, claim ledger |

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
| 1. Design | 这个路线怎样落成可执行设计？ | `study-design-builder` | selected `.aiss` `route`, seven `mida` declarations, `decision` declarations, `research_model.aiss`, `ai4ss_check_report.txt` | Data, literature, analysis |
| 2a. Data | 数据怎么来的，样本怎么变的？ | `research-data-builder` | derived data, `sample_flow.csv`, `merge_audit.csv`, `variable_provenance.csv`; for survey cleaning: `ddi-metadata.yaml`, `cleaning_contract`, execution audit | Analysis, methods review |
| 2b. Literature | 文献证据是不是一手来源？ | `literature-matrix` | `literature_candidate_discovery.csv`, `literature_matrix.csv`, optional compiled literature `.aiss` evidence | Design, writing scaffold |
| 3. Analysis | 第一批可检查结果怎么跑出来？ | `research-analysis-runner` | `analysis_readiness_check.csv`, scripts, tables, figures, logs, `analysis_run_manifest.csv` | Methods review |
| 4. Review | 结果解释有没有说过头？ | `methods-reviewer` | issue table, recommended checks, author decisions | Analysis, writing, revision |
| 5a. Writing scaffold | 作者怎样自己写得更稳？ | `academic-writing-scaffold` | claim ledger, section scaffold, citation gaps | Author drafting |
| 5b. Slides | 已验证证据怎样讲给听众？ | `research-slides-builder` | slide map, source map, evidence gaps | Author presentation |
| 5c. Revision | 返修有没有证据链？ | `reviewer-response` | revision matrix, revision plan, response scaffold | Data, analysis, writing |

## Shared Handoff Fields

Every skill should preserve these fields when available:

| field | meaning |
|---|---|
| `route_id` | Human-readable route key such as `R1`, preserved across sidecars |
| `route_decl_id` | Stable `.aiss` `route` declaration id from `research-starter` |
| `mida_id` | Stable `.aiss` `mida` declaration id from `study-design-builder`, when applicable |
| `decision_decl_id` | Stable `.aiss` `decision` declaration id for author-owned choices, when applicable |
| `mida_component` | `.aiss` `mida` component touched by this artifact, when applicable |
| `design_source` | Path to the design brief or decision register |
| `target_inquiry` | The declared inquiry, estimand, target quantity, construct, classification target, process-tracing claim, or synthesis question |
| `data_source` | Path to source data, derived data, or extracted source output |
| `analysis_plan_path` | Path to analysis plan, preregistration scaffold, or script plan |
| `readiness_status` | `ready`, `warn`, or `blocked` result from `analysis_readiness_check.csv` |
| `evidence_compile_status` | `compiled`, `needs_review`, `blocked`, or `not_applicable` status for literature evidence to `.aiss` compilation |
| `source_artifacts` | Literature matrix, source ledger, notes, PDFs, tables, figures, logs |
| `known_gaps` | Missing data, unresolved source, unclear design choice, or failed validation |
| `author_decisions` | Decisions that require researcher judgment |
| `validation_commands` | Commands run or exact commands still needed |
| `interpretation_boundary` | What the artifact can and cannot support |
| `next_skill_route` | The next skill or `ask_author` / `none` |

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
| `Report` | Claim ledger, source map, AI-use ledger, author decision point, and communication boundary |

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
