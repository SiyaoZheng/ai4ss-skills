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
| Workflow lifecycle | `route`, `mida`, `decision`, `event` | Records candidate/selected routes, MIDA declarations, automation assumptions, event-sourced runtime facts, and handoff state |
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
python3 dsl/scripts/aiss.py state path/to/research_model.aiss
python3 dsl/scripts/aiss.py transition path/to/research_model.aiss --event '{"type":"skill_started","at":"2026-07-05T00:00:00Z"}'
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
- `decision` declarations for human-accountable route, design, data, claim, or
  handoff choices
- `attribute` and `concept` declarations for the model vocabulary
- `causal` and `bridge` declarations when a causal or measurement claim matters
- a `model` declaration bundling the attributes, concepts, causal links, and
  bridges
- block-style `check` and `derive` declarations, for example:
- optional `event` declarations for state-machine facts emitted by the harness,
  skills, or a goal-cli watchdog, for example:

```aiss
check demo.check_reference_integrity {
  type: reference_integrity
  on: demo.platform_innovation
}

derive demo.derive_ibe_profile {
  type: ibe_profile
  from: demo.platform_innovation
}

event demo.event_public_sources_started {
  type: "skill_started"
  at: "2026-07-05T00:00:00Z"
  route: "demo.route_r1"
  skill: "public-data-sources"
  source: "goal-cli"
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
| Model | `mida` row, attributes, concepts, theta rules, relations, mechanisms, scope notes | design notes and assumption-register notes as cited sources |
| Inquiry | `mida` row, causal links, claim objects, bridge estimands | source notes that state target quantity, population, comparison, or time window |
| Data strategy | `mida` row, source objects, empirical objects, measurement bridges, artifacts | raw/derived data, cleaning logs, linkage logs, missingness diagnostics |
| Answer strategy | `mida` row, requested checks, derives, adapters when available | scripts, tables, figures, model objects, run logs |
| Diagnose | `mida` row, lint diagnostics, workflow/model diagnostics, bridge coverage, commensurability signals | robustness outputs and reviewer notes as cited artifacts |
| Redesign | `mida` row, changed IDs and structural diffs | assumption-register notes as cited sources |
| Report | `mida` row, bounded claim handoff, disclosure matrix, AI-use disclosure, direct-submission status, and manuscript package through checked IDs | AI-use ledger, slides, response drafts, replication package notes, and assumption notes as cited artifacts |

## Skillpack Integration

| local skill | relationship to `.aiss` v0.4 |
|---|---|
| `research-starter` | Creates or updates provisional `route` declarations; it does not finalize model claims |
| `study-design-builder` | Selects a `route`, writes the seven `mida` declarations with `mida_id`, records author choices as `decision` declarations with `decision_decl_id`, owns `research_model.aiss`, `ai4ss_check_report.txt`, and MIDA-to-model mapping |
| `literature-matrix` | Adds source-grounded `paper`, `source`, `span`, `claim`, `relation`, `concept`, `causal`, `bridge`, `check`, and `decision` declarations directly to `.aiss` or deterministic `.aiss` fragments |
| `research-data-builder` | Adds data `source`, `artifact`, `empirical`, `observation`, `coupling`, `bridge`, `check`, and `decision` declarations and routes survey cleaning through AI4SS DDI skills when relevant |
| `research-analysis-runner` | Requires `.aiss` readiness checks and links outputs back to model, concept, causal, bridge, or claim IDs |
| `top-journal-figures` | Links final R/ggplot2 paper figures to `.aiss` analysis artifacts, shared style profile, plotted data, source notes, captions, style-consistency checks, visual-integrity checks, vector-export status, and report-boundary decisions |
| `methods-reviewer` | Reviews `.aiss` lint/run output, bridge coverage, commensurability, and claim-support alignment, then records diagnostics as `.aiss` checks and decisions |
| `academic-writing-scaffold` | Builds report-boundary claim slots, TOP disclosure matrices, AI-disclosed manuscript assembly checklists, and working prose from checked `.aiss` IDs when requested |
| `research-slides-builder` | Uses checked `.aiss` concepts, bridges, and diagnosed limits as presentation source links |
| `reviewer-response` | Maps reviewer requests to MIDA elements, `.aiss` IDs, deviation logs, revision-transparency status, and AI-disclosed response working text |

Survey cleaning remains inside AI4SS through the DDI harness route:
`codebook-parse` -> `cleaning-contract` -> `cleaning-execute`.

## State-Machine Engine

The v0.4 entrypoint now exposes a deterministic state-machine layer:

- `aiss.py state` projects `aiss.machine_state.v0.4` from the selected route,
  seven MIDA rows, decisions, events, and heartbeat observations.
- `aiss.py transition --event ...` runs the reducer without writing. It returns
  before/after state plus suggested actions such as `dispatch_skill` or
  `watchdog_recover`.
- `aiss.py transition --event ... --write` appends a normalized `event`
  declaration to the `.aiss` file.

The engine deliberately does not execute skills, manage process locks, install
timers, or clean interrupted subprocesses. Those runtime duties belong to
goal-cli or an equivalent watchdog. `.aiss` remains the research-state source of
truth; goal-cli remains the heartbeat/tick executor.

## Appserver-Observed Entry Boundaries

The Codex appserver behavior test in `docs/appserver_behavior_tests.md`
confirmed the intended staged behavior for a blank-slate topic:

- `research-starter` is the correct zero-to-one entry skill. It creates
  candidate `.aiss` `route` declarations, a minimum viable study, continuation
  plans, and automation assumptions.
- `study-design-builder` is the route-to-design skill. With no selected route,
  it should auto-create or recover the strongest route; after a route exists,
  it writes the selected route, exactly seven `mida` declarations, decisions,
  and model/check declarations when warranted.

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
| G8b Paper figures are reproducible ggplot2 artifacts with one style profile | `.aiss` figure artifacts plus a shared style profile, R/ggplot2 scripts, plotted data, source notes, captions, style-consistency checks, visual-integrity checks, and vector exports | manuscript figures are screenshots, dashboard exports, helper-package black boxes, non-ggplot2 final artifacts, or visually inconsistent figure sets |
| G9 Reporting bounded | `.aiss` bounded claim/report declarations and AI-use ledger where required | unchecked causal/measurement claims become prose |
| G10 Transparency package declared | `.aiss` checks, artifacts, or decisions for registration, protocol, analysis plan, materials, data, code, reporting, FAIR metadata, and deviation logs | final paper package depends on undocumented availability or undisclosed deviations |
| G11 Replication package status declared | `.aiss` artifact/check declarations for scripts, runtime, data locators, logs, seeds, and restricted-access notes | outputs cannot be rerun or explained by another researcher |
| G12 AI-disclosed manuscript package bounded | disclosure matrix, AI contribution disclosure, human accountability status, submission policy check, direct-submission status, and manuscript assembly status | manuscript or response text is treated as submission-ready or no-AI while AI involvement, accountability, policy checks, or claim boundaries remain hidden |

## Evaluation

`scripts/run_factory_level_eval.py --clean` regenerates
`docs/factory_level_eval/` as a blinded packet and LLM-as-judge prompt package
for the full chain:

```text
rough topic -> .aiss route declarations -> .aiss MIDA declarations ->
.aiss model/check -> observed public-source acquisition ->
observed-data sample construction/check -> literature evidence gates ->
.aiss analysis readiness -> .aiss analysis artifacts ->
top-journal ggplot2 figure package -> transparency package ->
bounded claim handoff -> AI-disclosed manuscript package
```

That package checks artifact continuity and gate coverage only as judge
evidence. Reported eval scores must come from LLM-as-judge; deterministic
structural checks and expert audits are not eval scores. The package does not
prove field-level validity or replace independent expert review.
