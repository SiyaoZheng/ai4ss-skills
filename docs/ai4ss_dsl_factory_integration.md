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
| Workflow lifecycle | `route`, `mida`, `decision` | Records candidate/selected routes, MIDA declarations, author decisions, and handoff state |
| Evidence and discourse grounding | `paper`, `source`, `span`, `claim`, `relation`, `empirical`, `observation`, `coupling`, `artifact`, `adapter` | Records where concepts and claims come from and what empirical material they point to |
| Research model | `attribute`, `concept`, `causal`, `bridge`, `edge`, `model`, `check`, `derive` | Represents the MIDA-facing model, causal implications, measurement/causal bridges, requested checks, and derived diagnostics |

These are not separate DSLs. They are areas of one AST. Route and MIDA
declarations are first-class workflow declarations. CSV, Markdown, chat memory,
and ad hoc tables are not workflow state and must not be used as handoff
contracts. Research-model objects should carry source spans whenever they are
grounded in a design brief, literature row, dataset artifact, or analysis
output.

## Entry Point

The only supported deterministic entrypoint for skillpack validation is:

```bash
python3 dsl/scripts/aiss.py compile path/to/research_model.aiss
python3 dsl/scripts/aiss.py lint path/to/research_model.aiss
python3 dsl/scripts/aiss.py run path/to/research_model.aiss
```

There are no standalone `aiss_*` DSL entrypoints for the research-factory
skillpack. The skillpack contract is the v0.4 `aiss.py` entrypoint above.

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
- `decision` declarations for author-owned route, design, data, claim, or
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

| MIDA element | `.aiss` coverage | external artifacts referenced by `.aiss` |
|---|---|---|
| Model | `mida` row, attributes, concepts, theta rules, relations, mechanisms, scope notes | design notes and author decision notes as cited sources |
| Inquiry | `mida` row, causal links, claim objects, bridge estimands | source notes that state target quantity, population, comparison, or time window |
| Data strategy | `mida` row, source objects, empirical objects, measurement bridges, artifacts | raw/derived data, cleaning logs, linkage logs, missingness diagnostics |
| Answer strategy | `mida` row, requested checks, derives, adapters when available | scripts, tables, figures, model objects, run logs |
| Diagnose | `mida` row, lint diagnostics, workflow/model diagnostics, bridge coverage, commensurability signals | robustness outputs and reviewer notes as cited artifacts |
| Redesign | `mida` row, changed IDs and structural diffs | author decision notes as cited sources |
| Report | `mida` row, bounded claim handoff through checked IDs | AI-use ledger, slides, response drafts, and author notes as cited artifacts |

## Skillpack Integration

| local skill | relationship to `.aiss` v0.4 |
|---|---|
| `research-starter` | Creates or updates provisional `route` declarations; it does not finalize model claims |
| `study-design-builder` | Selects a `route`, writes the seven `mida` declarations with `mida_id`, records author choices as `decision` declarations with `decision_decl_id`, owns `research_model.aiss`, `ai4ss_check_report.txt`, and MIDA-to-model mapping |
| `literature-matrix` | Adds source-grounded `paper`, `source`, `span`, `claim`, `relation`, `concept`, `causal`, `bridge`, `check`, and `decision` declarations directly to `.aiss` or deterministic `.aiss` fragments |
| `research-data-builder` | Adds data `source`, `artifact`, `empirical`, `observation`, `coupling`, `bridge`, `check`, and `decision` declarations and routes survey cleaning through AI4SS DDI skills when relevant |
| `research-analysis-runner` | Requires `.aiss` readiness checks and links outputs back to model, concept, causal, bridge, or claim IDs |
| `methods-reviewer` | Reviews `.aiss` lint/run output, bridge coverage, commensurability, and claim-support alignment, then records diagnostics as `.aiss` checks and decisions |
| `academic-writing-scaffold` | Builds report-boundary claim slots from checked `.aiss` IDs; does not write final manuscript prose |
| `research-slides-builder` | Uses checked `.aiss` concepts, bridges, and diagnosed limits as presentation source links |
| `reviewer-response` | Maps reviewer requests to MIDA elements and `.aiss` IDs without writing final response prose |

Survey cleaning remains inside AI4SS through the DDI harness route:
`codebook-parse` -> `cleaning-contract` -> `cleaning-execute`.

## Appserver-Observed Entry Boundaries

The Codex appserver behavior test in `docs/appserver_behavior_tests.md`
confirmed the intended staged behavior for a blank-slate topic:

- `research-starter` is the correct zero-to-one entry skill. It creates
  candidate `.aiss` `route` declarations, a minimum viable study, stop reasons,
  and author decisions.
- `study-design-builder` is the route-to-design skill. With no selected route,
  it should stop or route back to `research-starter` / `ask_author`; after a
  route exists, it writes the selected route, exactly seven `mida` declarations,
  decisions, and model/check declarations when warranted.

## Factory Gates

| gate | required artifact | failure signal |
|---|---|---|
| G1 Research object exists | `.aiss` `route` declarations | only topic prose or ad hoc tables |
| G2 Design declared | selected `.aiss` `route` plus seven `mida` declarations | no selected route, incomplete MIDA, or no stable IDs |
| G3 Unified workflow/model checks run | `ai4ss_check_report.txt` or logged `aiss.py compile/lint/run` output | parse errors, lint errors, missing references, missing spans, missing MIDA coverage |
| G4 Empirical bridge declared | `bridge` rows or equivalent design fields | causal or measurement claim lacks empirical bridge |
| G5 Literature evidence compiled when it changes the model | `.aiss` source/span/claim/model declarations generated by `compile_evidence.py` or equivalent checked `.aiss` output | sources revise the model only in prose or ad hoc tables |
| G6 Data contract exists when data are transformed | `.aiss` data source, artifact, empirical, observation, coupling, bridge, and check declarations | raw-to-analysis path depends on memory or undocumented recodes |
| G7 Analysis readiness passed | `.aiss` readiness `check` declarations | clean data do not match inquiry or bridge alignment is unchecked |
| G8 Analysis links back to design | `.aiss` analysis artifact/check/derive declarations with model/claim references | tables or figures cannot be traced to declared inquiry |
| G9 Reporting bounded | `.aiss` bounded claim/report declarations and AI-use ledger where required | unchecked causal/measurement claims become prose |

## Evaluation

`scripts/run_factory_level_eval.py --clean` regenerates
`docs/factory_level_eval/` as a deterministic structural evaluation of the full
chain:

```text
rough topic -> .aiss route declarations -> .aiss MIDA declarations ->
.aiss model/check ->
literature/data gates -> .aiss analysis readiness -> .aiss analysis artifacts ->
bounded claim handoff
```

That evaluation checks artifact continuity and gate coverage. It does not prove
field-level validity or replace independent expert review.
