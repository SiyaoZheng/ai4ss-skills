# AI4SS DSL Factory Integration

This note defines the current local contract for the AI4SS research-factory
skillpack.

## Decision

There is one workflow DSL: `.aiss` version `0.4`.

The old split between a source-grounded PaperAST language and a separate
research-model language is fused in v0.4. A valid research-factory `.aiss` file
now compiles into one canonical AST:

```text
aiss.unified_ast.v0.4
```

That AST has connected workflow, evidence, and model regions:

| region | declarations | role |
|---|---|---|
| Workflow lifecycle | `route`, `mida`, `decision` | Records candidate/selected routes, MIDA declarations, required gates, and handoff state |
| Evidence and discourse grounding | `paper`, `source`, `span`, `claim`, `relation`, `empirical`, `observation`, `coupling`, `artifact`, `adapter` | Records where concepts and claims come from and what empirical material they point to |
| Research model | `attribute`, `concept`, `causal`, `bridge`, `edge`, `model`, `check`, `derive` | Represents the MIDA-facing model, causal implications, measurement/causal bridges, requested checks, and derived diagnostics |

These are not separate DSLs. They are areas of one AST. Route cards and MIDA
declarations are first-class workflow declarations, while CSV/Markdown sidecars
are readable mirrors for humans and validators. Research-model objects should
carry source spans whenever they are grounded in a design brief, literature row,
dataset artifact, or analysis output.

## Entry Point

The only supported deterministic entrypoint for skillpack validation is:

```bash
python3 dsl/scripts/aiss.py compile path/to/research_model.aiss
python3 dsl/scripts/aiss.py lint path/to/research_model.aiss
python3 dsl/scripts/aiss.py run path/to/research_model.aiss
python3 dsl/scripts/aiss.py transition path/to/research_model.aiss
```

There are no standalone `aiss_*` DSL entrypoints for the research-factory
skillpack. The skillpack contract is the v0.4 `aiss.py` entrypoint above.
The `transition` command is the deterministic paper-artifact state machine: it
reads the current `.aiss` object and emits `full_paper_goal`,
`current_state.paper_artifact_state`, `paper_artifact_gaps`, and
`next_paper_artifact`. `required_artifacts` and `blocked_reasons` remain in the
JSON so relay audits can find the owner and evidence needed for a blocked gate,
but they do not define completion.

## Required Shape

A research-factory model must start with:

```aiss
aiss version "0.4"
```

A production `research_model.aiss` should normally include:

- one `paper` declaration for the represented research object
- one or more `source` declarations for design briefs, literature rows, data
  artifacts, code, or notes
- `span` declarations used by routes, MIDA rows, decisions, concepts, claims,
  empirical objects, couplings, attributes, causal links, or bridges
- one or more `route` declarations from `research-starter`; provisional routes
  use `status: candidate`, and the design route uses `status: selected`
- seven `mida` declarations for the selected route: `model`, `inquiry`,
  `data_strategy`, `answer_strategy`, `diagnose`, `redesign`, and
  `report_boundary`
- `decision` declarations for workflow-gated route, design, data, claim, or
  handoff choices
- `attribute` and `concept` declarations for the model vocabulary
- `causal` and `bridge` declarations when a causal or measurement claim matters
- a `model` declaration bundling the attributes, concepts, causal links, and
  bridges
- block-style `check` and `derive` declarations, for example:

```aiss
check demo.check_reference_integrity {
  type: reference_integrity
  on: demo.platform_innovation
}

derive demo.derive_ibe_profile {
  type: ibe_profile
  from: demo.platform_innovation
}
```

Do not use the former local research-model extension. Do not write old infix
forms such as `check theta_completeness on demo.model`.

## Relation To MIDA

MIDA remains the methodology spine:

```text
Declare MIDA -> Diagnose -> Redesign -> Report with bounded claims
```

The unified `.aiss` AST is the computable research object inside that spine.

| MIDA element | `.aiss` coverage | sidecars still needed |
|---|---|---|
| Model | `mida` row, attributes, concepts, theta rules, relations, mechanisms, scope notes | design brief view, decision-register view |
| Inquiry | `mida` row, causal links, claim objects, bridge estimands | target quantity, population, comparison, time window view |
| Data strategy | `mida` row, source objects, empirical objects, measurement bridges, artifacts | sample flow, cleaning contract, linkage audit, missingness notes |
| Answer strategy | `mida` row, requested checks, derives, adapters when available | analysis scripts, table/figure shells, run manifest |
| Diagnose | `mida` row, lint diagnostics, workflow/model diagnostics, bridge coverage, commensurability signals | methods-review issue table, robustness outputs |
| Redesign | `mida` row, changed IDs and structural diffs | required-gate view |
| Report | `mida` row, bounded claim handoff through checked IDs | paper-section artifacts, figure/table bundle, references, full paper source, full paper PDF; claim and AI-use ledgers remain supporting gates where required |

## Skillpack Integration

| local skill | relationship to `.aiss` v0.4 |
|---|---|
| `research-starter` | Creates or updates provisional `route` declarations and mirrors them as route cards with `route_decl_id`; it does not finalize model claims |
| `study-design-builder` | Selects a `route`, writes the seven `mida` declarations with `mida_id`, records workflow-gated choices as `decision` declarations with `decision_decl_id`, owns `research_model.aiss`, `ai4ss_check_report.txt`, and MIDA-to-model mapping when conceptual or causal structure matters |
| `literature-matrix` | Produces source-grounded rows and, when a source affects the model, compiles deterministic evidence fragments with `compile_evidence.py` |
| `research-data-builder` | Preserves `ai4ss_model_path`, concept/causal/bridge IDs, and routes survey cleaning through `codebook-parse`, `cleaning-contract`, and `cleaning-execute` when relevant |
| `research-analysis-runner` | Requires `analysis_readiness_check.csv` and links outputs back to model, concept, causal, bridge, or claim IDs |
| `methods-reviewer` | Reviews `.aiss` lint/run output, bridge coverage, commensurability, and claim-support alignment |
| `academic-writing-scaffold` | Builds claim ledgers from checked IDs; does not write final manuscript prose |
| `research-slides-builder` | Uses checked concepts, bridges, and diagnosed limits as source-map entries |
| `reviewer-response` | Maps reviewer requests to MIDA elements and `.aiss` IDs without writing final response prose |

## Appserver-Observed Entry Boundaries

The Codex appserver behavior test in `docs/appserver_behavior_tests.md`
confirmed the intended staged behavior for a blank-slate topic:

- `research-starter` is the correct zero-to-one entry skill. It creates route
  cards, a minimum viable study, stop reasons, and optional candidate `.aiss`
  `route` declarations.
- `study-design-builder` is the route-to-design skill. With no selected route,
  it should stop or route back to `research-starter` / `last_skill`; after a
  route exists, it writes the selected route, exactly seven `mida` declarations,
  decisions, and model/check declarations when warranted.

## Factory Gates

| gate | required artifact | failure signal |
|---|---|---|
| G1 Research object exists | `.aiss` `route` declarations, optionally mirrored in `research_starter_packet.md` and route cards | only topic prose |
| G2 Design declared | selected `.aiss` `route` plus seven `mida` declarations, optionally mirrored in `study_design_declaration.csv` | no selected route, incomplete MIDA, or no stable IDs |
| G3 Unified workflow/model checks run | `ai4ss_check_report.txt` or logged `aiss.py compile/lint/run` output | parse errors, lint errors, missing references, missing spans, missing MIDA coverage |
| G4 Empirical bridge declared | `bridge` rows or equivalent design fields | causal or measurement claim lacks empirical bridge |
| G5 Literature evidence compiled when it changes the model | `evidence_table_path`, `compiled_ai4ss_path`, `evidence_compile_status` | source rows revise the model only in prose or saved `.aiss` differs from `compile_evidence.py` output |
| G6 Data contract exists when data are transformed | DDI metadata, cleaning contract, execution audit, sample flow | raw-to-analysis path depends on memory or undocumented recodes |
| G7 Analysis readiness passed | `analysis_readiness_check.csv` | clean data do not match inquiry or bridge alignment is unchecked |
| G8 Analysis links back to design | analysis manifest with model/claim references | tables or figures cannot be traced to declared inquiry |
| G9 Reporting bounded | paper artifact sequence, full paper source, full paper PDF, and supporting ledgers where required | unchecked causal/measurement claims become prose or the run ends without a paper |

## Evaluation

`scripts/run_factory_level_eval.py --clean` regenerates
`docs/factory_level_eval/` as a deterministic structural evaluation of the full
chain:

```text
rough topic -> .aiss route declarations -> .aiss MIDA declarations ->
.aiss model/check ->
literature/data gates -> analysis readiness -> analysis manifest ->
full paper artifact
```

That evaluation checks artifact continuity and gate coverage. It does not prove
field-level validity or replace independent expert review.

The state-machine relay audit is the lower-level transition test:

```bash
PYTHONPATH=scripts python3 scripts/test_factory_contracts.py
PYTHONPATH=scripts python3 scripts/run_skill_handoff_audit_fixtures.py
```

It uses `docs/evals/factory-relay/fixtures/valid_relay.aiss` as the known-good
relay and mutates it into failure cases. The audit must reject missing MIDA
report boundaries, misrouted repair rows, parallel Markdown/CSV/JSON workflow
state, missing downstream consumers, dropped empirical artifact links, route
drift, and synthetic/demo fallback analysis.
